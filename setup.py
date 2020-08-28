from setuptools import setup, find_packages

setup(
        name = 'ipybd',
        version = '0.9.9',
        description = 'Powerful data cleaner for biodiversity',
        license = 'GPL-3.0 License',
        author = 'Xu Zhoufeng',
        author_email = 'xu_zhoufeng@hotmail.com',
        url = 'https://github.com/leisux/ipybd',
        packages = find_packages(),
        package_data = {
            '':['lib/*.json', 'lib/*.xlsx']
            },
        platforms = 'any',
        python_requires=">=3.6.1",        
        keywords = (
            'biodiversity', 
            'scientificName', 
            'herbarium', 
            'specimens',
            'bdcleaner'
            ),
        install_requires=[
            'pandas',
            'tqdm',
            'prompt_toolkit',
            'requests',
            'aiohttp'
        ]
)