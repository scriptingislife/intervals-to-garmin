# intervals-to-garmin

This project aims to sync activities from a Wahoo bike computer with Garmin Connect. It uses [intervals.icu](https://intervals.icu/) as the facilitator.

## Setup

1. Clone the GitHub repo

```shell
git clone https://github.com/scriptingislife/intervals-to-garmin
```

2. Find your intervals.icu API key on [the settings page](https://intervals.icu/settings). Also note the Athlete ID for the next step. Use the command below to create an SSM Parameter to store the key.

```shell
aws ssm put-parameter \
  --name "/cycling/intervals/api_key" \
  --value "YOUR_INTERVALS_API_KEY" \
  --type SecureString
  ```

3. Log in to Garmin using [garth](https://github.com/matin/garth). Install [uv](https://github.com/astral-sh/uv) if it is not already installed.

```shell
uvx garth login
```

4. Create another SSM Parameter to store the Garmin Connect session data.

```shell
aws ssm put-parameter \
  --name "/cycling/garmin/session" \
  --value "YOUR_GARTH_OUTPUT_STRING" \
  --type SecureString
```

5. Build and deploy the rest of the infrastructure. When prompted input the Athlete ID also found in the settings page.

```shell
sam build
sam deploy --guided
```

## Removal

To delete the sample application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
sam delete --stack-name "intervals-to-garmin"
```

Delete the parameters `/cycling/intervals/api_key` and `/cycling/garmin/session` manually.

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for an introduction to SAM specification, the SAM CLI, and serverless application concepts.
