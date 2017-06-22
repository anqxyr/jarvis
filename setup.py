import setuptools

VERSIONFILE = 'jarvis/version.py'
with open(VERSIONFILE) as file:
    version = file.readline()
    version = version.split('=')[-1].strip().strip("'")

setuptools.setup(
    name='jarvis',
    version=version,
    description='Snarky bot for scp-wiki irc channels.',
    long_description='',
    url='https://github.com/anqxyr/jarvis/',
    author='anqxyr',
    author_email='anqxyr@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4'],
    packages=['jarvis', 'jarvis/modules'],
    package_data={'jarvis': [
        'lexicon.yaml',
        'resources/help.template',
        'resources/lexicon/*',
        'resources/templates/*']},
    tests_require=[
        'pytest>=3.0.2',
        'pytest-cov',
        'python-coveralls'],
    install_requires=[
        'arrow',
        'dominate',
        'google-api-python-client',
        'jinja2',
        'logbook',
        'markovify',
        'natural',
        'oauth2client==3.0.0',
        'pyaml',
        'sopel',
        'tweepy',
        'wikipedia',
        'pint',
        'faker',
    ],
)
