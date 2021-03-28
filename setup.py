from setuptools import setup

setup(
   name='bt_futu_store',
   version='1.0',
   description='Futu API store for backtrader',
   url='',
   author='Damon Yuan',
   author_email='damon.yuan.dev@gmail.com',
   license='MIT',
   packages=['btfutu'],
   install_requires=['backtrader', 'futu-api'],
)