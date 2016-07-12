import setuptools

setuptools.setup(
    name='jarvis',
    version='0.9',
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
    package_data={'jarvis': ['lexicon.yaml']},
    install_requires=[
        'sopel',
        'wikipedia',
        'dominate',
        'pyaml',
        'logbook',
        'google-api-python-client'],
)
