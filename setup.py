import setuptools

setuptools.setup(
    name='pyscp_bot',
    version='0.0.3',
    description='Snarky bot for scp-wiki irc channels.',
    long_description='',
    url='https://github.com/anqxyr/pyscp_bot/',
    author='anqxyr',
    author_email='anqxyr@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4'],
    packages=['pyscp_bot'],
    install_requires=[
        'pyscp',
        'sopel'],
)
