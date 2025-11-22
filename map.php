<!DOCTYPE html>
<html>
<head>
    <title>Location Map Viewer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        #map {
            height: 500px;
            width: 800px;
            margin-top: 20px;
            margin: 20px auto;
            border-radius: 40px;
        }
        .input-container {
            margin-bottom: 10px;
        }
        input[type="text"] {
            width: 300px;
            padding: 8px;
        }
        button {
            padding: 8px 15px;
            background-color: #4285F4;
            color: white;
            border: none;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>Location Map Viewer</h1>
    <form method="post">
        <?php for ($i = 1; $i <= 5; $i++): ?>
            <div class="input-container">
                <label for="location<?php echo $i; ?>">Location <?php echo $i; ?>:</label>
                <input type="text" id="location<?php echo $i; ?>" name="locations[]" 
                       value="<?php echo isset($_POST['locations'][$i-1]) ? htmlspecialchars($_POST['locations'][$i-1]) : ''; ?>">
            </div>
        <?php endfor; ?>
        <button type="submit">Show Map</button>
    </form>

    <?php
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && !empty($_POST['locations'])) {
        // Filter out empty locations
        $locations = array_filter($_POST['locations']);
        
        if (!empty($locations)) {
            echo '<div id="map"></div>';
            
            // Load Google Maps API
            echo '<script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyDFLnUQcWcPCurZdF-WKLvXXNhJrjDjxCM&callback=initMap" async defer></script>';
            
            // JavaScript to display the map
            echo '<script>
                function initMap() {
                    var geocoder = new google.maps.Geocoder();
                    var map;
                    var bounds = new google.maps.LatLngBounds();
                    var markers = [];
                    var locationCount = 0;
                    var processedCount = 0;
                    
                    // Count non-empty locations
                    locationCount = ' . count($locations) . ';
                    
                    if (locationCount === 0) return;
                    
                    // Initialize map with temporary center
                    map = new google.maps.Map(document.getElementById("map"), {
                        zoom: 8
                    });
                    
                    // Process each location
                    ';
                    
            foreach ($locations as $location) {
                echo 'geocoder.geocode({ address: "' . addslashes($location) . '" }, function(results, status) {
                        if (status === "OK") {
                            var marker = new google.maps.Marker({
                                map: map,
                                position: results[0].geometry.location,
                                title: "' . addslashes($location) . '"
                            });
                            markers.push(marker);
                            bounds.extend(results[0].geometry.location);
                        }
                        processedCount++;
                        if (processedCount === locationCount) {
                            if (markers.length > 0) {
                                map.fitBounds(bounds);
                                // Add a small padding
                                map.panToBounds(bounds);
                            }
                        }
                    });';
            }
            
            echo '
                }
            </script>';
        }
    }
    ?>
</body>
</html>