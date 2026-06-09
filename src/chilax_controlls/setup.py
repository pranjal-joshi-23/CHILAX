from setuptools import find_packages, setup

package_name = 'chilax_controlls'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pranjaljoshi',
    maintainer_email='pranjaljoshi@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "joint_position_publisher = chilax_controlls.joint_position_publisher:main",
            # "main = chilax_controlls.main:main"
            "test_controller = chilax_controlls.test_controller:main",
            "user_keyboard_input = chilax_controlls.user_keyboard_input:main",
            "keyboard_controller = chilax_controlls.keyboard_controlles_mapping:main"
        ],
    },
)
