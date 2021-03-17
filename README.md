# TrueWiki

[![GitHub License](https://img.shields.io/github/license/TrueBrain/TrueWiki)](https://github.com/TrueBrain/TrueWiki/blob/master/LICENSE)
[![GitHub Tag](https://img.shields.io/github/v/tag/TrueBrain/TrueWiki?include_prereleases&label=stable)](https://github.com/TrueBrain/TrueWiki/releases)
[![GitHub commits since latest release](https://img.shields.io/github/commits-since/TrueBrain/TrueWiki/latest/master)](https://github.com/TrueBrain/TrueWiki/commits/master)

[![GitHub Workflow Status (Testing)](https://img.shields.io/github/workflow/status/TrueBrain/TrueWiki/Testing/master?label=master)](https://github.com/TrueBrain/TrueWiki/actions?query=workflow%3ATesting)

TrueWiki is an opinionated wikitext server similar to [MediaWiki](https://github.com/wikimedia/mediawiki) and/or [gollum](https://github.com/gollum/gollum).
As default storage it uses GitHub (instead of a database).

- [Opinionated](#opinionated)
- [Configuration](#configuration)
- [Configuration / GitHub](#using-github)
- [Configuration / GitLab](#using-gitlab)
- [Development](#development)
- [Why Yet-Another-Wiki-Server](#why-yet-another-wiki-server)

## Opinionated

TrueWiki iterates over what MediaWiki offers to bring a more modern approach to a wiki.
These opinions are described below.

### Wikitext

Although most of the wikitext is compatible with the one implemented by MediaWiki, TrueWiki is a lot more strict and accepts less mistakes.

For example, `[[ File:en/MyFile.png ]]` is an error, as there should not be a space between `[[` and `File`.
Other errors, like an unknown variable, links to pages that do not exist, etc, are also reported to the user.
This in the hope to motivate people to both write better wikitext, but also to fix mistakes that otherwise go unnoticed.

If there is one or more error, a badge is shown over "View Source", to inform anyone using the wiki that the page contains errors.

### Translations

While MediaWiki uses separate Wikis for each language, TrueWiki includes them in a single wiki.
This leaves it open to the wiki owner which language is the primary, and TrueWiki doesn't care about it.
Additionally, with the help of the `Translation` namespace, TrueWiki helps to make navigating between different translations of the same page.
It also informs if a link is of a different language, by postfixing the link with the language.

This is all done to make it easier for translators to translate the wiki, and easier for readers to know what to expect.

### Folders

TrueWiki uses a folder-tree structure to organise pages (similar to Confluence or other commercial Wikis).
There are no uncategorised / unlinked / free-floating pages as in MediaWiki.

Folders can easily be navigated, and complement Categories and Namespaces.

### Namespaces

TrueWiki implements namespaces similar to MediaWiki, with the exception users of the wiki cannot create their own namespaces.
Custom namespaces are replaced by a folder-tree structure.

Namespaces have a specific function, and can render heavily altered pages depending on the namespace.
For example, the `File` namespace allows uploading of files, where no other namespace allows this.

#### Category

`[[Category:en/MyCategory]]` marks a Category / File / Page / Template as being part of that category.

`[[:Category:en/MyCategory]]` links to the Category.

#### File

This is mostly identical to what MediaWiki implements.

`[[File:en/MyFile.png]]` embeds the image in your page.
Parameters like `thumb`, `frame`, `left`, `link=` etc are all supported.

`[[:File:en/MyFile.png]]` adds a link to the file.

Files have to be either PNG (with `.png` extension), GIF (with `.gif` extension), or JPEG (with `.jpeg` extension).
No other formats are supported, and you have to upload the correct type for the given extension.

#### Folder

This is to navigate the folder structure of the wiki.
It is meant as alternative of custom namespaces as used by MediaWiki, while giving clear overview of what pages exist.
All pages have in their bottom right a link to the folder their page is located in.

#### Page

Similar to MediaWiki's `Main` namespace; this contains all the pages.
This is the default namespace, meaning that `[[en/Page]]` implies the `Page` namespace.

#### Template

Similar to MediaWiki's `Template` namespace; this contains all the templates which can be transcluded on Pages.
There is no real difference between `Template` and `Page`, except that `{{MyTemplate}}` uses `Template` namespace by default.
One can use `{{Page:MyPage}}` to transclude a Page.

#### Translation

The translation system used by TrueWiki.

`[[Translation:en/MyPage]]` marks the page as a translation (or the English version) or a Page.
All translations of this page automatically pick up on the new translation and add them to their header.

## Configuration

TrueWiki has two methods of configuration: runtime options and wiki configuration file.

The runtime options defines how TrueWiki (the server) should run.
The wiki configuration file defines how the wiki should look and feel.

### Runtime options

Running `python -m truewiki --help` will give a detailed overview of all the settings.

```
Usage: __main__.py [OPTIONS]

Options:
  --sentry-dsn TEXT               Sentry DSN.
  --sentry-environment TEXT       Environment we are running in.
  --bind TEXT                     The IP to bind the server to  [default: ::1,
                                  127.0.0.1]

  --port INTEGER                  Port of the web server  [default: 80]
  --storage [github|gitlab|git|local]
                                  [required]
  --frontend-url TEXT             URL of the frontend, used for creating
                                  absolute links in the sitemap.xml

  --reload-secret TEXT            Secret to allow an index reload. Always use
                                  this via an environment variable!

  --cache-metadata-file TEXT      File used to cache metadata.  [default:
                                  .cache_metadata.json]

  --storage-folder DIRECTORY      Folder to use for storage.  [default:
                                  ./data]

  --storage-git-username TEXT     Username to use when creating commits.
                                  [default: Librarian]

  --storage-git-email TEXT        Email to use when creating commits.
                                  [default: wiki@localhost]

  --storage-github-url URL        Repository URL on GitHub.  [default:
                                  https://github.com/TrueBrain/wiki-example]

  --storage-github-history-url URL
                                  Repository URL on GitHub to visit history
                                  (defaults to --storage-github-url).

  --storage-github-private-key TEXT
                                  Base64-encoded private key to access
                                  GitHub.Always use this via an environment
                                  variable!

  --storage-gitlab-url URL        Repository URL on Gitlab.  [default:
                                  https://gitlab.com/TrueBrain/wiki-
                                  example.git/]

  --storage-gitlab-history-url URL
                                  Repository URL on Gitlab to visit history
                                  (defaults to --storage-gitlab-url).

  --storage-gitlab-private-key TEXT
                                  Base64-encoded private key to access
                                  Gitlab.Always use this via an environment
                                  variable!

  --user [developer|github|gitlab]
                                  User backend to use (can have multiple).
                                  [required]

  --user-session-expire SECONDS   Time for a session to expire (measured from
                                  the moment of login).  [default: 50400]

  --user-login-expire SECONDS     Time for a login attempt to expire.
                                  [default: 600]

  --user-session-expire-schedule SECONDS
                                  The interval between check if a user session
                                  is expired.  [default: 900]

  --user-github-client-id TEXT    GitHub client ID. (user=github only)
  --user-github-client-secret TEXT
                                  GitHub client secret. Always use this via an
                                  environment variable! (user=github only)

  --user-gitlab-client-id TEXT    Gitlab client ID. (user=gitlab only)
  --user-gitlab-client-secret TEXT
                                  Gitlab client secret. Always use this via an
                                  environment variable! (user=gitlab only)

  --cache-page-folder TEXT        Folder used to cache rendered pages.
  --validate-all                  Validate all mediawiki files and report all
                                  errors

  -h, --help                      Show this message and exit.
```

#### Using GitHub

Setting `--storage` and `--user` to `github` will run TrueWiki on a [GitHub](https://github.com) git repository as backend.

By default, it will checkout the [wiki-example](https://github.com/TrueBrain/wiki-example) project, and edits will not persist (a restart will remove any edits).

With `--storage-github-url` you can change this to your own repository; but in order for TrueWiki to push changes, you will have to setup an SSH key with write permissions.

The easiest way to do this is via a [Deployment Key](https://docs.github.com/en/developers/overview/managing-deploy-keys#deploy-keys) on GitHub.
`TRUEWIKI_STORAGE_GITHUB_PRIVATE_KEY` should be set to the base64-encoded private key matching the deployment key.
`--storage-github-url` should be set to the SSH url of your GitHub repository (for example: `git@github.com:TrueBrain/wiki-example.git`).
With this, TrueWiki will automatically push changes to the GitHub repository, making your wiki persistent.

#### Using GitLab

Setting `--storage` and `--user` to `gitlab` will run TrueWiki on a [GitLab](https://gitlab.com) git repository as backend.

By default, it will checkout the [wiki-example](https://gitlab.com/TrueBrain/wiki-example) project, and edits will not persist (a restart will remove any edits).

With `--storage-gitlab-url` you can change this to your own repository; but in order for TrueWiki to push changes, you will have to setup an SSH key with write permissions.

The easiest way to do this is via a [SSH Key](https://docs.gitlab.com/ee/ssh/) on GitLab.
`TRUEWIKI_STORAGE_GITLAB_PRIVATE_KEY` should be set to the base64-encoded private key matching the deployment key.
`--storage-gitlab-url` should be set to the SSH url of your GitLab repository (for example: `git@gitlab.com:TrueBrain/wiki-example.git`).
With this, TrueWiki will automatically push changes to the GitLab repository, making your wiki persistent.

### Wiki configuration file

This tells TrueWiki how to render the wiki pages.
It allows for configuration of CSS, Javascript, header, footer and more.
For detailed information about the options and what they do, please see the example project:

https://github.com/TrueBrain/wiki-example/blob/master/.truewiki.yml

## Development

This server is written in Python 3.8 with aiohttp.

### Running a local server

#### Dependencies

- Python3.8 or higher.

#### Preparing your venv

To start it, you are advised to first create a virtualenv:

```bash
python3 -m venv .env
.env/bin/pip install -r requirements.txt
```

#### Preparing a data folder

TrueWiki needs to read its data from somewhere, and this normally is a git repository in the `data` folder.
It should contain the following folders (TrueWiki will create required folders if needed):

- `Category` - For the files in the Category namespace; should contain `.mediawiki` files.
- `File` - For the files in the File namespace; can contain any file.
- `Page` - For the files in the default namespace; should contain `.mediawiki` files.
- `Template` - For the files in the Template namespace; should contain `.mediawiki` files.

#### Starting a local server

You can start the HTTP server by running:

```bash
.env/bin/python -m truewiki
```

This will start the server on port 8000 for you to work with locally.

### Running via docker

```bash
docker build -t truebrain/truewiki:local .
docker run --rm -p 127.0.0.1:8000:80 -v "`pwd`/data:/data" -v "`pwd`/cache:/cache" truebrain/truewiki:local
```

## Why Yet-Another-Wiki-Server

I have been responsible for the [MediaWiki](https://github.com/wikimedia/mediawiki) installation on https://wiki.openttd.org/ from ~2005 till 2020.
One thing became clear: it is very difficult to keep it up-to-date and to find quality extensions that live for more than a few years.
For example, finding a good quality OAuth2 extension is not only difficult, their workflows are also often weird and errors are difficult to trace.

In 2019 I started with migrating all OpenTTD services to AWS.
The main issue with running a MediaWiki installation in AWS, that is is non-trivial.
You need either an expensive database via RDS, or you need to run an EC2 instance yourself.
If you go for an RDS, scaling up MediaWiki is also non-trivial, as it needs persistent storage for uploads.
In the end, it was concluded that running MediaWiki on AWS would be both expensive and requires a lot of custom maintenance.
In contrast, all other services run on AWS ECS, where a tag on GitHub causes a new version to be rolled out.

So, we set out to find an alternative.
With the experience we have had with for example [BaNaNaS](https://github.com/OpenTTD/BaNaNaS) we ideally would like to store all the data in git.
This is mostly as data in git is easier for more people to maintain, then a database where very few people have access to.
Also, the wiki of OpenTTD was not big enough (~5000 pages) to really need a database to support it.
As extra bonus, we would favour any system that could easily be cached.

The software closest to this is [gollum](https://github.com/gollum/gollum).
Although gollum appears to do exactly what we want, especially as wikitext is supported via [WikiCloth](https://github.com/usemodj/WikiCloth), reality turned out to be something else.
Although it does support wikitext, or a subset thereof, it does not support templates.
This is a huge issue for any real wiki, as templates make a wiki of any decent size possible.
Initially we did hack in support for templates, but as it is written in Ruby, not a language any of the people involved knew sufficiently to make any decent contribution, it only added more issues than it resolved.
In the end, it was decided this was not a road to go.

This made me interested in how difficult it would be to write this ourself.
A quick search showed the existence of [wikitextparser](https://github.com/5j9/wikitextparser), written in Python, the programming languages all OpenTTD services are written in.
This library seems to be able to parse wikitext just fine, the repository exists for many years, the author is still active, and has a 100% coverage.
In short this library is absolutely amazing.
It took ~4 hours to make a proof of concept, to show we can render HTML via this library from wikitext.
So, [wikitexthtml](https://github.com/TrueBrain/wikitexthtml) was born.

The next week or so was spend in finding bugs in [wikitextparser](https://github.com/5j9/wikitextparser) and [wikitexthtml](https://github.com/TrueBrain/wikitexthtml), while we were running the current content of the OpenTTD wiki through it.
Nothing groundbreaking, just the normal edge-cases you get when parsing a wiki that has been around for 15+ years with many different people thinking they can write wikitext.
It was also where we found out that wikitext has not really a specification; it is more of a: what-ever the PHP implementation does.
A [rust library](https://docs.rs/parse_wiki_text/0.1.5/parse_wiki_text/) for parsing wikitext has an excellent rant about this, expressing exactly how I feel.

In the end, this repository was born.
It renders pages faster than MediaWiki serves pages from its cache (TrueWiki: ~30ms, MediaWiki: ~120ms).

The wikitext supported is far from completely, and it is easily to find many edge-cases where it fails.
But mostly, this can be solved by informing the user, while creating the page, something is going wrong.
Often the fixes are trivial, and good user-feedback avoids this.
This means that with only supporting a subset of wikitext, all of the 5000+ pages on the OpenTTD wiki as it was in 2020 could be rendered to HTML in nearly the same way as MediaWiki can.

And that is the history of TrueWiki.

Owh, and the name? Well, frosch123 helped out a lot with exporting the OpenTTD wiki from MediaWiki to our on-disk format.
And he joked it would be a good name. TrueBrain .. TrueWiki .. get it?
I agree, it is an excellent name.
Thank you so much frosch123 for the help with this repository!
