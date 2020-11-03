# TrueWiki

[![GitHub License](https://img.shields.io/github/license/TrueBrain/TrueWiki)](https://github.com/TrueBrain/TrueWiki/blob/master/LICENSE)
[![GitHub Tag](https://img.shields.io/github/v/tag/TrueBrain/TrueWiki?include_prereleases&label=stable)](https://github.com/TrueBrain/TrueWiki/releases)
[![GitHub commits since latest release](https://img.shields.io/github/commits-since/TrueBrain/TrueWiki/latest/master)](https://github.com/TrueBrain/TrueWiki/commits/master)

[![GitHub Workflow Status (Testing)](https://img.shields.io/github/workflow/status/TrueBrain/TrueWiki/Testing/master?label=master)](https://github.com/TrueBrain/TrueWiki/actions?query=workflow%3ATesting)

TrueWiki is a wikitext server similar to [mediawiki](https://github.com/wikimedia/mediawiki) and/or [gollum](https://github.com/gollum/gollum).
As default storage it uses git (instead of a database).

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
It should contain the following folders:

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

I have been responsible for the [mediawiki](https://github.com/wikimedia/mediawiki) installation on https://wiki.openttd.org/ from ~2005 till 2020.
One thing became clear: it is very difficult to keep it up-to-date and to find quality extensions that live for more than a few years.
For example, finding a good quality OAuth2 extension is not only difficult, their workflows are also often weird and errors are difficult to trace.

In 2019 I started with migrating all OpenTTD services to AWS.
The main issue with running a mediawiki installation in AWS, that is is non-trivial.
You need either an expensive database via RDS, or you need to run an EC2 instance yourself.
If you go for an RDS, scaling up mediawiki is also non-trivial, as it needs persistent storage for uploads.
In the end, it was concluded that running mediawiki on AWS would be both expensive and requires a lot of custom maintenance.
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
It renders pages faster than mediawiki serves pages from its cache (TrueWiki: ~30ms, mediawiki: ~120ms).

The wikitext supported is far from completely, and it is easily to find many edge-cases where it fails.
But mostly, this can be solved by informing the user, while creating the page, something is going wrong.
Often the fixes are trivial, and good user-feedback avoids this.
This means that with only supporting a subset of wikitext, all of the 5000+ pages on the OpenTTD wiki as it was in 2020 could be rendered to HTML in nearly the same way as mediawiki can.

And that is the history of TrueWiki.

Owh, and the name? Well, frosch123 helped out a lot with exporting the OpenTTD wiki from mediawiki to our on-disk format.
And he joked it would be a good name. TrueBrain .. TrueWiki .. get it?
I agree, it is an excellent name.
Thank you so much frosch123 for the help with this repository!
