from gitpwnd import app  # defined in gitpwnd/__init__.py

#################
# Server config #
#################

app.secret_key = "blah-doesn't-matter"

if __name__ == "__main__":
    # Note: that the '0.0.0.0' makes the server publicly accessible, be careful friend
    app.run(host='0.0.0.0', ssl_context='adhoc')
