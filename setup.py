from setuptools import setup, find_packages

# populate setup requires from requiers.pip
with open('requires.pip', 'r') as r:
    install_requires = []
    dependency_links = []
    for line in r:
        if not line:
            continue
        if '#egg=' in line:
            dependency_links.append(line[:])
            line = line.split('#egg=')[1]
        install_requires.append(line)


setup(
    name='craigslist',
    version='0.0.1',
    description='craigslist crawler on Pomp',
    long_description='craigslist crawler on Pomp',
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Django",
        "Framework :: Pomp",
    ],
    author='Evgeniy Tatarkin',
    author_email='tatarkin.evg@gmail.com',
    packages=find_packages(),
    install_requires=install_requires,
    dependency_links=dependency_links,
    entry_points="""
    [console_scripts]
    manage = craigslist.manage:main
    """,
)
