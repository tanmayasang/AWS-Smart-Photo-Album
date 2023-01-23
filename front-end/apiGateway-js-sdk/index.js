var apigClient = apigClientFactory.newClient({apiKey: 'FAtyYtn1u51h6a8OSy8xv75D3trxkuDP2vv967YT'});
window.SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition

function voiceSearch(){
    if ('SpeechRecognition' in window) {
        console.log("SpeechRecognition is Working");
    } else {
        console.log("SpeechRecognition is Not Working");
    }
    
    var inputSearchQuery = document.getElementById("search_query");
    const recognition = new window.SpeechRecognition();
    //recognition.continuous = true;

    micButton = document.getElementById("mic_search");  
    
    if (micButton.innerHTML == "mic") {
        recognition.start();
    } else if (micButton.innerHTML == "mic_off"){
        recognition.stop();
    }

    recognition.addEventListener("start", function() {
        micButton.innerHTML = "mic_off";
        console.log("Recording.....");
    });

    recognition.addEventListener("end", function() {
        console.log("Stopping recording.");
        micButton.innerHTML = "mic";
    });

    recognition.addEventListener("result", resultOfSpeechRecognition);
    function resultOfSpeechRecognition(event) {
        const current = event.resultIndex;
        transcript = event.results[current][0].transcript;
        inputSearchQuery.value = transcript;
        console.log("transcript : ", transcript)
    }
}




function textSearch() {
    var searchText = document.getElementById('search_query');
    if (!searchText.value) {
        alert('Please enter a valid text or voice input!');
    } else {
        searchText = searchText.value.trim().toLowerCase();
        console.log('Searching Photos....');
        searchPhotos(searchText);
    }
    
}

function searchPhotos(searchText) {

    console.log(searchText);
    document.getElementById('search_query').value = searchText;
    document.getElementById('photos_search_results').innerHTML = "<h4 style=\"text-align:center\">";

    var params = {
        'q' : searchText
    };
    
    apigClient.searchGet(params, {}, {})
        .then(function(result) {
            console.log("Result : ", result);

            results = result["data"]["body"]["results"];
            console.log("results : ", results);

            var photosDiv = document.getElementById("photos_search_results");
            photosDiv.innerHTML = "";

            var n;
            for (n = 0; n < results.length; n++) {
                url_split = results[n].url.split('/');
                imageName = url_split[url_split.length - 1];

                photosDiv.innerHTML += '<figure style="display: inline-block"><img src="' + results[n].url + '" style="width:25%"><figcaption>' + imageName + '</figcaption></figure>';
            }

        }).catch(function(result) {
            console.log(result);
        });
}

function uploadPhoto() {
    var filePath = (document.getElementById('uploaded_file').value).split("\\");
    var fileName = filePath[filePath.length - 1];
    
    var customLabels = document.getElementById('custom_labels');
    if (!customLabels.innerText == "") {
    }
    console.log(fileName);
    console.log(customLabels.value);

    var reader = new FileReader();
    var file = document.getElementById('uploaded_file').files[0];
    console.log('File : ', file);
    document.getElementById('uploaded_file').value = "";

    if ((filePath == "") || (!['png', 'jpg', 'jpeg'].includes(filePath[2].split(".")[1]))) {
        alert("Please upload a valid .png/.jpg/.jpeg file!");
    } else {

        var params = {
            'x-amz-meta-customLabels': customLabels.value,
            'bucket': 'b2cloudbucket',
            'key': filePath[2]
        };
        var additionalParams = {
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            }
        };
        
        reader.onload = function (event) {
            body = {
                'image': `${btoa(event.target.result)}`,
                'bucket': 'b2cloudbucket',
                'key': <YOUR API KEY>,
                'contentType': file.type,
                'x-amz-meta-customLabels': customLabels.value
            };
            console.log('Reader body : ', body);
            return apigClient.folderItemPut(params, body, additionalParams)
            .then(function(result) {
                console.log(result);
            })
            .catch(function(error) {
                console.log(error);
            })
        }
        reader.readAsBinaryString(file);
    }
}