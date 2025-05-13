#!/bin/bash


# Create a python module/package, ask for the module name
echo "Enter the module name"
read module_name

# Create the module directory
mkdir $module_name

# Create the __init__.py file
touch $module_name/__init__.py