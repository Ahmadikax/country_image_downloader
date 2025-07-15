<?php
/**
 * Country Image Downloader Wrapper
 * 
 * This script provides a web interface to run the country image downloader Python script.
 * It allows users to download country images without having to use the command line.
 */

// Set error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Set time limit to 0 (no limit) as downloading images can take time
set_time_limit(0);

// Define constants
define('SCRIPT_PATH', __DIR__ . '/country_image_downloader.py');
define('COUNTRY_LIST_PATH', __DIR__ . '/country_list.txt');
define('OUTPUT_DIR', __DIR__ . '/images');
define('LOG_FILE', __DIR__ . '/country_image_downloader.log');

// Create output directory if it doesn't exist
if (!file_exists(OUTPUT_DIR)) {
    mkdir(OUTPUT_DIR, 0755, true);
}

// Function to check if Python is installed
function isPythonInstalled() {
    $command = 'python --version 2>&1';
    $output = [];
    $returnCode = 0;
    exec($command, $output, $returnCode);
    
    return $returnCode === 0;
}

// Function to check if required Python packages are installed
function arePackagesInstalled() {
    $command = 'python -c "import selenium, requests, PIL, tqdm" 2>&1';
    $output = [];
    $returnCode = 0;
    exec($command, $output, $returnCode);
    
    return $returnCode === 0;
}

// Function to install required packages
function installPackages() {
    $command = 'pip install -r ' . __DIR__ . '/requirements.txt 2>&1';
    $output = [];
    $returnCode = 0;
    exec($command, $output, $returnCode);
    
    return [
        'success' => $returnCode === 0,
        'output' => implode("\n", $output)
    ];
}

// Function to run the downloader script
function runDownloader($options = []) {
    $command = 'python ' . SCRIPT_PATH;
    
    // Add options
    foreach ($options as $key => $value) {
        if (is_bool($value) && $value) {
            $command .= ' --' . $key;
        } elseif (!is_bool($value)) {
            $command .= ' --' . $key . ' "' . escapeshellarg($value) . '"';
        }
    }
    
    // Redirect stderr to stdout and capture output
    $command .= ' 2>&1';
    
    // Execute the command
    $output = [];
    $returnCode = 0;
    exec($command, $output, $returnCode);
    
    return [
        'success' => $returnCode === 0,
        'output' => implode("\n", $output)
    ];
}

// Function to get the list of countries from the country list file
function getCountries() {
    $countries = [];
    
    if (file_exists(COUNTRY_LIST_PATH)) {
        $lines = file(COUNTRY_LIST_PATH, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        
        foreach ($lines as $line) {
            $parts = explode(':', $line, 2);
            if (count($parts) === 2) {
                $id = trim($parts[0]);
                $name = trim($parts[1]);
                $countries[] = [
                    'id' => $id,
                    'name' => $name
                ];
            }
        }
    }
    
    return $countries;
}

// Function to get the log file content
function getLogContent() {
    if (file_exists(LOG_FILE)) {
        return file_get_contents(LOG_FILE);
    }
    
    return '';
}

// Handle form submission
$result = null;
$message = '';
$logContent = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Check if Python is installed
    if (!isPythonInstalled()) {
        $message = 'Error: Python is not installed or not in PATH.';
    } else {
        // Check if required packages are installed
        if (!arePackagesInstalled()) {
            $installResult = installPackages();
            if (!$installResult['success']) {
                $message = 'Error installing required packages: ' . $installResult['output'];
            }
        }
        
        // If everything is set up, run the downloader
        if (empty($message)) {
            $options = [];
            
            // Process form inputs
            if (isset($_POST['headless']) && $_POST['headless'] === 'on') {
                $options['headless'] = true;
            }
            
            if (isset($_POST['browser']) && in_array($_POST['browser'], ['chrome', 'firefox'])) {
                $options['browser'] = $_POST['browser'];
            }
            
            if (isset($_POST['max_images']) && is_numeric($_POST['max_images'])) {
                $options['max-images'] = (int)$_POST['max_images'];
            }
            
            if (isset($_POST['country_id']) && !empty($_POST['country_id'])) {
                $options['country-id'] = $_POST['country_id'];
            }
            
            if (isset($_POST['country_name']) && !empty($_POST['country_name'])) {
                $options['country-name'] = $_POST['country_name'];
            }
            
            if (isset($_POST['debug']) && $_POST['debug'] === 'on') {
                $options['debug'] = true;
            }
            
            // Set output directory
            $options['output-dir'] = OUTPUT_DIR;
            
            // Run the downloader
            $result = runDownloader($options);
            
            if ($result['success']) {
                $message = 'Download completed successfully!';
            } else {
                $message = 'Error running the downloader: ' . $result['output'];
            }
            
            // Get log content
            $logContent = getLogContent();
        }
    }
}

// Get the list of countries
$countries = getCountries();

// Get the list of downloaded images
$downloadedImages = [];
if (file_exists(OUTPUT_DIR)) {
    $dirs = glob(OUTPUT_DIR . '/*', GLOB_ONLYDIR);
    foreach ($dirs as $dir) {
        $countryName = basename($dir);
        $images = glob($dir . '/*.{jpg,jpeg,png,webp,gif}', GLOB_BRACE);
        $zipFiles = glob($dir . '/*.zip');
        
        $downloadedImages[] = [
            'country' => $countryName,
            'images' => $images,
            'zipFiles' => $zipFiles,
            'count' => count($images)
        ];
    }
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Country Image Downloader</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .card {
            background: #fff;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input[type="text"],
        input[type="number"],
        select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        input[type="checkbox"] {
            margin-right: 10px;
        }
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #2980b9;
        }
        .alert {
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .alert-success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-danger {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .log-container {
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            height: 300px;
            overflow-y: auto;
            font-family: monospace;
            white-space: pre-wrap;
        }
        .tabs {
            display: flex;
            border-bottom: 1px solid #ddd;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 15px;
            cursor: pointer;
            border: 1px solid transparent;
            border-bottom: none;
            margin-bottom: -1px;
        }
        .tab.active {
            border-color: #ddd;
            border-radius: 4px 4px 0 0;
            background: #fff;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            grid-gap: 15px;
        }
        .gallery-item {
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
        }
        .gallery-item img {
            width: 100%;
            height: 150px;
            object-fit: cover;
        }
        .gallery-item .caption {
            padding: 10px;
            text-align: center;
            background: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Country Image Downloader</h1>
        
        <?php if (!empty($message)): ?>
            <div class="alert <?php echo $result && $result['success'] ? 'alert-success' : 'alert-danger'; ?>">
                <?php echo $message; ?>
            </div>
        <?php endif; ?>
        
        <div class="tabs">
            <div class="tab active" data-tab="download">Download Images</div>
            <div class="tab" data-tab="gallery">Image Gallery</div>
            <div class="tab" data-tab="log">Log</div>
        </div>
        
        <div class="tab-content active" id="download">
            <div class="card">
                <h2>Download Country Images</h2>
                <form method="post" action="">
                    <div class="form-group">
                        <label for="country_select">Select Country:</label>
                        <select id="country_select" onchange="updateCountryFields()">
                            <option value="">-- Select a country --</option>
                            <?php foreach ($countries as $country): ?>
                                <option value="<?php echo htmlspecialchars($country['id']); ?>" data-name="<?php echo htmlspecialchars($country['name']); ?>">
                                    <?php echo htmlspecialchars($country['name']); ?> (ID: <?php echo htmlspecialchars($country['id']); ?>)
                                </option>
                            <?php endforeach; ?>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="country_id">Country ID:</label>
                        <input type="text" id="country_id" name="country_id" placeholder="Enter country ID">
                    </div>
                    
                    <div class="form-group">
                        <label for="country_name">Country Name:</label>
                        <input type="text" id="country_name" name="country_name" placeholder="Enter country name">
                    </div>
                    
                    <div class="form-group">
                        <label for="browser">Browser:</label>
                        <select id="browser" name="browser">
                            <option value="chrome">Chrome</option>
                            <option value="firefox">Firefox</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="max_images">Maximum Images per Country:</label>
                        <input type="number" id="max_images" name="max_images" value="10" min="1" max="100">
                    </div>
                    
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="headless" checked> Run in headless mode
                        </label>
                    </div>
                    
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="debug"> Enable debug logging
                        </label>
                    </div>
                    
                    <button type="submit">Download Images</button>
                </form>
            </div>
        </div>
        
        <div class="tab-content" id="gallery">
            <div class="card">
                <h2>Downloaded Images</h2>
                
                <?php if (empty($downloadedImages)): ?>
                    <p>No images have been downloaded yet.</p>
                <?php else: ?>
                    <?php foreach ($downloadedImages as $country): ?>
                        <h3><?php echo htmlspecialchars($country['country']); ?> (<?php echo count($country['images']); ?> images)</h3>
                        
                        <?php if (!empty($country['zipFiles'])): ?>
                            <p>
                                Download ZIP: 
                                <?php foreach ($country['zipFiles'] as $zipFile): ?>
                                    <a href="<?php echo str_replace(__DIR__, '', $zipFile); ?>" download><?php echo basename($zipFile); ?></a>
                                <?php endforeach; ?>
                            </p>
                        <?php endif; ?>
                        
                        <div class="gallery">
                            <?php foreach ($country['images'] as $image): ?>
                                <div class="gallery-item">
                                    <img src="<?php echo str_replace(__DIR__, '', $image); ?>" alt="<?php echo basename($image); ?>">
                                    <div class="caption"><?php echo basename($image); ?></div>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>
        </div>
        
        <div class="tab-content" id="log">
            <div class="card">
                <h2>Log Output</h2>
                <div class="log-container"><?php echo htmlspecialchars($logContent); ?></div>
            </div>
        </div>
    </div>
    
    <script>
        // Function to update country fields when a country is selected
        function updateCountryFields() {
            const select = document.getElementById('country_select');
            const countryIdField = document.getElementById('country_id');
            const countryNameField = document.getElementById('country_name');
            
            if (select.value) {
                countryIdField.value = select.value;
                countryNameField.value = select.options[select.selectedIndex].dataset.name;
            } else {
                countryIdField.value = '';
                countryNameField.value = '';
            }
        }
        
        // Tab functionality
        document.addEventListener('DOMContentLoaded', function() {
            const tabs = document.querySelectorAll('.tab');
            
            tabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    // Remove active class from all tabs
                    tabs.forEach(t => t.classList.remove('active'));
                    
                    // Add active class to clicked tab
                    this.classList.add('active');
                    
                    // Hide all tab content
                    document.querySelectorAll('.tab-content').forEach(content => {
                        content.classList.remove('active');
                    });
                    
                    // Show the corresponding tab content
                    const tabId = this.dataset.tab;
                    document.getElementById(tabId).classList.add('active');
                });
            });
        });
    </script>
</body>
</html>