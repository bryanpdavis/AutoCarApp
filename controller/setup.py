from setuptools import setup

setup(name='autocarapp',
      version='0.1',
      description='Remote RPi car controlled with logitech game controllers.',
      url='https://github.com/bryanpdavis/AutoCarApp',
      author='Bryan Davis',
      author_email='bryanpdavis@gmail.com',
      license='MIT',
      packages=['AutoCarApp'],
      install_requires=[
          'requests',
          'pygame',
          'beautifultable',
      ],
      zip_safe=False)