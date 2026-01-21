# Public Data Extractor for Meetup.com

Do you organise an event on meetup.com? Would you like basic details of the event to be available as Open Data for reuse elsewhere?

(Public details only - this does NOT extract any information about the people attending your events.)

This is an unofficial tool not endorsed by Meetup.com - use at your own risk!

## Install

```commandline
pip install public-data-extractor-for-meetup-com
```

## Configure

Log into https://www.meetup.com/ and go to "View Profile".
You'll be at a URL like: https://www.meetup.com/members/123456789/
That number is your member ID.
Set it as the environmental Variable `MEETUP_COM_AUTHORIZED_MEMBER_ID`

Go to https://www.meetup.com/graphql/oauth/list/ and create a new API client.

Set the Client Key as the environmental Variable `MEETUP_COM_YOUR_CLIENT_KEY`

Create a new signing key for the client (Make sure you save the private certificate as you won't see it again!)
Set it as the environmental Variable `MEETUP_COM_PRIVATE_SIGNING_KEY`

## Run

Run:

```commandline
python -m publicdataextractorformeetupcom extractgroup your_group_slug output_directory
```

The output directory will then hold files with public information that you can publish.

## Run & Host on GitHub

You can run this automatically and host it on GitHub.

Make a new public GitHub repository, selecting the "Add Readme" option.

In settings, Secrets and Variables, Actions, add the following repository secrets:

* MEETUP_COM_AUTHORIZED_MEMBER_ID
* MEETUP_COM_YOUR_CLIENT_KEY
* MEETUP_COM_PRIVATE_SIGNING_KEY

The values should be as described in the "Configure" section above.

In settings, Secrets and Variables, Actions, add the following repository variables:

* MEETUP_COM_GROUP_URL_NAME - The group you want to import, from the https://www.meetup.com/group_name/ URL. Just the `group_name` part.

Go to Settings, GitHub pages and change the source to "GitHub Actions".

Create a file `.github/workflows/build.yml` and copy the contents of the `github_workflow.yml` file into it. Commit this file and push it to GitHub.

Go to Actions in the repository, and make sure the first run finishes successfully. It can take a few minutes for it to actually start.

You should now be able to view `out.json` on your GitHub pages URL. (Go back to Settings, GitHub pages to find the URL.)

## For Developers

The GraphQL Playground at https://www.meetup.com/graphql/playground/#graphQl-playground is very handy to explore.

