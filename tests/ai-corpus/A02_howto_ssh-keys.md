# Setting Up SSH Keys for GitHub

If you are still typing your password every time you push to GitHub, this guide is for you. SSH keys let you authenticate securely without a password prompt, and setting them up takes about five minutes.

## Why SSH keys?

Passwords can be guessed, phished, or leaked. An SSH key pair is different: the private key never leaves your machine, and the public key is useless without it. Once configured, authentication is seamless, secure, and automatic.

## Step 1: Check for existing keys

Open a terminal and run:

```
ls -la ~/.ssh
```

If you see files named `id_ed25519` and `id_ed25519.pub`, you already have a key pair and can skip to Step 3.

## Step 2: Generate a new key

Run the following command, using a comment that identifies the machine:

```
ssh-keygen -t ed25519 -C "work laptop"
```

Press Enter to accept the default file location. You will be prompted for a passphrase. Choose a strong one; it protects your key if your machine is ever compromised.

## Step 3: Add the key to the SSH agent

Start the agent and add your key:

```
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

## Step 4: Add the public key to GitHub

Copy the contents of your public key:

```
cat ~/.ssh/id_ed25519.pub
```

In GitHub, go to Settings, then SSH and GPG keys, then New SSH key. Paste the key, give it a descriptive title, and save.

## Step 5: Test the connection

```
ssh -T github
```

Here `github` is the host alias from your SSH config; without one, use the standard git-over-SSH address from GitHub's documentation. You should see a message confirming successful authentication. If you do, you are done.

## Troubleshooting

If the connection fails, make sure the agent is running, verify that you copied the entire public key, and confirm that your remote URL uses the SSH format rather than HTTPS.

## Conclusion

With SSH keys in place, you get faster workflows, stronger security, and one less password to remember. It is a small setup step that pays off every single day.
