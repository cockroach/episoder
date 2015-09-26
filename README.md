episoder is a tool to tell you about new episodes of your favourite TV shows.

#### Installation

You can install episoder through [pypi](https://pypi.python.org/pypi/episoder) (using `easy_install` or `pip`) or by
downloading the tarball from here and running `easy_install episoder-0.7.1.tar.gz`

#### Configuration

The configuration file at `~/.episoder` contains your default settings for episoder. After installing episoder
`man episoder` will help you with the configuration.

#### Using episoder

To use episoder you will typically:

* Create a cron job to have your database rebuilt once a day using `episoder update`
* Add `episoder` to your `~/.bashrc`, `~/.bash_profile`, `/etc/bash.bashrc` or `/etc/profile` if you want to see
your upcoming shows every time you start a shell. Consult your shell's documentation to find out which file you
want to use.
