from setuptools import setup
import os
REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]

setup(
   name='bt_futu_store',
   version='1.0',
   description='Futu API store for backtrader',
   license='MIT',
   url='',
   author='Damon Yuan',
   author_email='damon.yuan.dev@gmail.com',
   packages=['btfutu'],
   install_requires=REQUIREMENTS
)