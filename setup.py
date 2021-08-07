from setuptools import setup, find_packages

with open("README.md", "r", encoding='utf-8') as fh:
    long_description= fh.read()

setup(
        name = 'ipybd',
        version = '1.0.20',
        description = 'Powerful data cleaner for biodiversity',
        license = 'GPL-3.0 License',
        author = 'Xu Zhoufeng',
        author_email = 'xu_zhoufeng@hotmail.com',
        url = 'https://github.com/leisux/ipybd',
        packages = find_packages(),
        long_description=long_description,
        long_description_content_type="text/markdown",
        package_data = {
            '':['lib/*.py', 'lib/*.json', 'lib/*.xlsx', 'label/*.py', 'label/*.mustache', 'label/*.css']
            },
        platforms = 'any',
        python_requires=">=3.6.1",
        keywords = (
            'biodiversity',
            'scientificName',
            'herbarium',
            'specimens',
            'bdcleaner',
            'labelmaker'
            ),
        install_requires=[
            'pandas>=1.1.1',
            'openpyxl>=3.0.7',
            'tqdm>=4.40.2',
            'prompt_toolkit>=3.0.5',
            'requests>=2.21.0',
            'aiohttp>=3.6.2',
            'arrow>=0.16.0',
            'pystache>=0.5.4',
            'pystrich>=0.8',
            'jsonschema>=2.6.0'
        ]
)
