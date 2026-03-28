# aws-project-1
install aws cli before using the instructions provided here: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
# paste the following into a terminal
aws login
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Submit file for review
aws s3 cp {insert_json_or_csv_file} s3://sam-app-feedbackbucket-6l36mzbhlexz/incoming/{json_or_csv_file}
# Review feedback manually
aws lambda invoke \\
  --function-name sam-app-SubmitReviewFunction-0UnenRXP12Vv \\
  --cli-binary-format raw-in-base64-out \\
  --payload '{
    "review_id": "insert_id_here",
    "decision": "APPROVED",
    "reviewer": "insert_email_address"
  }' \\
  response.json
# Example input files provided
