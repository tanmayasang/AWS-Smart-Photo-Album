# AWS-Smart-Photo-Album
A photo album web application, that can be searched using natural language through both text and voice. Utilizes Amazon Lex, ElasticSearch, and Rekognition to create an intelligent search layer to query a user's photos for people, objects, actions, landmarks and more.

The web app has the following components
1. Lambda Function “index-photos” gets triggered by any object being added to an S3 bucket via /PUT API and index it in an ElasticSearch domain
2. The /PUT API requires additional parameters of x-amz-meta-customLabels and API key to label the photos stored in S3 and ElasticSearch
3. Lambda Function “search-photos" has the following workflow :
      3.1 It gets triggered whenever the user clicks on th search icon after entering a search phrase (Example :"Show me flowers")
      3.2 It disambiguates the input query using the Lex bot.
      3.3 It searches ElasticSearch for the photos which match extracted keywords and returns the photos to the user. 
      
4. .yaml file is the CloudFormation Template to automate the creation of all elements from scratch. 
5. Front end folder consists of the front end files and javascript code. The apigClient.js file is the javascript SDK of the REST API's created in API Gateway

 
