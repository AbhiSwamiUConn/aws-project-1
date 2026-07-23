# aws-project-1
install aws cli before using the instructions provided here: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html  
# paste the following into a terminal
aws login  
python3 -m venv venv  
source venv/bin/activate  
pip install -r requirements.txt  
sam build  
sam deploy  
# Submit file for review
aws s3 cp {json_or_csv_file} s3://{feedback_bucket_name}/incoming/{json_or_csv_file}
# Review feedback manually 
Select the feedback review id from the dynamodb reviews table    
aws lambda invoke \\  
  --function-name {submit_review_lambda_function_name} \\  
  --cli-binary-format raw-in-base64-out \\  
  --payload '{  
    "review_id": "insert_id_here",  
    "decision": "APPROVED",  
    "reviewer": "insert_email_address"  
  }' \\  
  response.json  
# Example input files in repo
