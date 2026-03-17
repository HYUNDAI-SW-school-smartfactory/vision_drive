from setuptools import setup

package_name = 'agv_comm'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'requests'],
    zip_safe=True,
    maintainer='agung',
    maintainer_email='jbjokagd@gmail.com',
    description='ROS2 HTTP communication node for AGV and vision server',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'comm_node = agv_comm.comm_node:main',
        ],
    },
)
