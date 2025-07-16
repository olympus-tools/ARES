from setuptools import setup, find_packages

# Load requirements from requirements.txt
def parse_requirements(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]
requirements = parse_requirements('requirements.txt')

setup(
    name='ares',
    version='0.1.0',
    description='Automated Rapid Embedded Simulation',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Andrä Carotta',
    author_email='not_yet@ares.com',
    url='https://github.com/AndraeCarotta/ARES',
    license='GNU LGPLv3',
    install_requires=requirements,
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: POSIX :: Linux',
        'Environment :: Console',
    ],
)
