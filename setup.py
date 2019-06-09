from setuptools import setup, find_packages

setup(name='atdb_plot',
      version='1.0.0',
      description='Plotting ATDB data',
      url='',
      author='Nico Vermaas',
      author_email='nvermaas@astron.nl',
      license='BSD',
      install_requires=['plotly','requests','psycopg2'],
      packages=find_packages(),
      entry_points={
            'console_scripts': [
                  'atdb_plot=atdb_plot.atdb_plot:main',
                  'atdb_read=atdb_statistics.atdb_read:main',
            ],
      }
      )