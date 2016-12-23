# Extract data from Craigslist.org by python3 and [pomp](https://bitbucket.org/estin/pomp) framework

Example how to build scalable cluster of web crawlers with centralized jobs queue on python3.

- [redis](http://redis.io/) for queue management with unique jobs
- Apache [Kafka](http://kafka.apache.org/) for committing gathered data
- [django](https://www.djangoproject.com/) with postgres database backend to store and visualize gathered data
- grafana with kamon dashboards for metric collecting via [kamon-io/docker-grafana-graphite](https://github.com/kamon-io/docker-grafana-graphite)
- [pomp](https://bitbucket.org/estin/pomp) lightweight web scraping framework
- [docker-compose](https://docs.docker.com/compose/) to run all of this zoo in one machine

Crawler instance uses:

- latest python3
- works on asyncio
- [aiohttp](http://aiohttp.readthedocs.org/en/stable/) for async fetch html pages from craigslist.org
- [lxml](http://lxml.de/) for parsing content

[Screencast](https://drive.google.com/file/d/0BzRf6g_VWuIjZDUxMGc1Q1ZScFk/view?usp=sharing) without audio.

## Notice

This software is not associated with Craigslist and for research purposes only.
Please check Craigslist [terms of use](https://www.craigslist.org/about/terms.of.use) and [robots.txt](http://craigslist.org/robots.txt).

## Keep in mind

All this stuff is overhead stack of technologies to scrape data from [Craigslist.org](https://www.craigslist.org/).

You can get all of you need from [Craigslist.org](https://www.craigslist.org/) in few steps with urllib/requests/etc + re/lxml/beautifulsoup/etc.

But this example is a good entry point to make own cluster of web crawlers like [Scrapy Cluster](https://github.com/istresearch/scrapy-cluster).

Item's price saved and represented in cents.

Crawler have some issues when trying to parse some pages for example purposes of exception handling.

Hard-coded in crawler sources:

- Craigslist's cities to scrape are: newyork, sfbay, chicago
- max number of list's pages to scrape is 3, first 3 pages from pagination
- max number of concurrent requests for one crawler instance is 3
- concurrent parse content by 2 workers, one crawler instance would be extract data by 2 workers

## Installation

Prepare:

    $ git clone https://github.com/estin/pomp-craigslist-example.git
    $ cd pomp-craigslist-example
    $ mkdir logs
    $ docker-compose pull

Install crawler and requirements:

    $ docker-compose run --rm crawler python3 setup.py develop --user

Create database and admin user for django app:

    $ docker-compose run --rm dataview manage dataview migrate
    $ docker-compose run --rm dataview sh -c "echo \"from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'myemail@example.com', 'admin')\" | manage dataview shell"

Configure grafana/kamon dashboard to view metrics:

- login to dashboard <http://localhost:8090/>
- go to `Data Sources` section <http://localhost:8090/datasources>
and click on `add new` or open link <http://localhost:8090/datasources/new>
- set field `Name` to `graphite`
- set field `Url` to `http://localhost:81/`
- click on `Add` button
- then import `dashboard.json` from this repo on <http://localhost:8090/import/dashboard> page

## Usage

Run:

    $ docker-compose up -d

Check status:

    $ docker-compose ps

Start new crawling session:

    $ docker-compose run --rm crawler manage session kidbike "search/bia?is_paid=all&search_distance_type=mi&query=kid+bike"

Where `kidbike` is the crawling session id and other part is the target query from browser url.

This command put next requests to the job's queue:

- <https://newyork.craigslist.org/search/bia?is_paid=all&search_distance_type=mi&query=kid+bike>
- <https://sfbay.craigslist.org/search/bia?is_paid=all&search_distance_type=mi&query=kid+bike>
- <https://chicago.craigslist.org/search/bia?is_paid=all&search_distance_type=mi&query=kid+bike>

And then check (with username: admin and pass: admin):

- <http://localhost:8080/admin> to view parsed and imported data to the postgres, do not forget periodically refresh the page
- <http://localhost:8090/> to view metrics in kamon dashboard
- logs in `./logs` directory or `docker-compose logs <service name>`


Increase crawler instances to speedup:

    $ docker-compose scale crawler=2

Start another one crawling session:

    $ docker-compose run --rm crawler manage session mountainbike "search/bia?is_paid=all&search_distance_type=mi&query=mountain+bike"


## Project structure

- entry point craigslist/manage.py
- `craigslist` crawler, downloader, pipelines, middlewares and utils
- `dataview` django app
- `dashboard.json` kamon dashboard
- `tests` unit tests for `craigslist`

```
$ tree -I "*.pyc|__pycache__"
.
├── base-compose.yml
├── craigslist
│   ├── crawler.py
│   ├── downloader.py
│   ├── __init__.py
│   ├── item.py
│   ├── log.py
│   ├── manage.py
│   ├── middleware.py
│   ├── pipeline.py
│   ├── queue.py
│   └── utils.py
├── dashboard.json
├── dataview
│   ├── __init__.py
│   ├── items
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── __init__.py
│   │   ├── management
│   │   │   └── commands
│   │   │       ├── dbimport.py
│   │   │       └── __init__.py
│   │   ├── migrations
│   │   │   ├── 0001_initial.py
│   │   │   └── __init__.py
│   │   ├── models.py
│   │   ├── tests.py
│   │   └── views.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── docker-compose.yml
├── README.md
├── requires.pip
├── setup.py
└── tests
    ├── data
    │   ├── item.html
    │   └── list.html
    ├── test_crawler.py
    ├── test_downloader.py
    ├── test_pipeline.py
    ├── test_queue.py
    └── utils.py

8 directories, 37 files
```


## TODO

- [ ] draw architecture diagram
- [ ] use asyncio kafka implementation
- [ ] fix kafka node not ready error on startup
- [ ] use native kafka consumer poll when doing bulk import data to postgres
- [ ] gather metrics of queue size only by one crawler instance or separate django management command

## License

(The MIT License)

Copyright (c) 2016 Evgeniy Tatarkin

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
