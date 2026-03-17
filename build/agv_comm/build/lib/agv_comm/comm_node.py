import os
from typing import List

import requests
import rclpy
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node


class AGVCommNode(Node):
    """ROS2 node for AGV <-> Vision Server HTTP communication."""

    def __init__(self) -> None:
        super().__init__('agv_comm_node')

        self.declare_parameter('server_host', '192.168.0.10')
        self.declare_parameter('server_port', 8000)
        self.declare_parameter('poll_interval_sec', 1.0)
        self.declare_parameter('http_timeout_sec', 2.0)
        self.declare_parameter('startup_image_path', '')
        self.declare_parameter('image_trigger_path', '')

        server_host = self.get_parameter('server_host').value
        server_port = int(self.get_parameter('server_port').value)
        poll_interval_sec = float(self.get_parameter('poll_interval_sec').value)
        self.http_timeout_sec = float(self.get_parameter('http_timeout_sec').value)
        self.startup_image_path = str(self.get_parameter('startup_image_path').value)

        self.base_url = f'http://{server_host}:{server_port}'
        self.command_url = f'{self.base_url}/command'
        self.analyze_url = f'{self.base_url}/analyze'
        self.current_route: List[str] = []

        self.poll_timer = self.create_timer(poll_interval_sec, self.poll_command)
        self.add_on_set_parameters_callback(self._on_parameter_changed)

        self.get_logger().info(
            f'AGVCommNode started. server={self.base_url}, poll={poll_interval_sec}s, '
            f'timeout={self.http_timeout_sec}s'
        )
        self.get_logger().info(
            "Image trigger: set parameter 'image_trigger_path' with an absolute image path."
        )

        if self.startup_image_path:
            self.send_image(self.startup_image_path)

    def _on_parameter_changed(self, parameters) -> SetParametersResult:
        """Handle runtime image trigger using ROS parameter update."""
        for parameter in parameters:
            if parameter.name == 'image_trigger_path':
                image_path = str(parameter.value).strip()
                if image_path:
                    self.send_image(image_path)
        return SetParametersResult(successful=True)

    def poll_command(self) -> None:
        """Periodically fetch the latest route command from vision server."""
        try:
            response = requests.get(self.command_url, timeout=self.http_timeout_sec)
            response.raise_for_status()
            payload = response.json()

            route = payload.get('route', [])
            if not isinstance(route, list):
                self.get_logger().warning('Invalid route format from server (expected list).')
                return

            if route != self.current_route:
                self.current_route = route
                self.get_logger().info(f'Received route: {self.current_route}')
        except requests.RequestException as exc:
            self.get_logger().warning(f'GET /command failed: {exc}')
        except ValueError as exc:
            self.get_logger().warning(f'Invalid JSON from /command: {exc}')

    def send_image(self, image_path: str) -> None:
        """Send an image file to vision server (/analyze)."""
        if not image_path:
            self.get_logger().warning('send_image called with empty image path.')
            return

        if not os.path.isfile(image_path):
            self.get_logger().warning(f'Image file not found: {image_path}')
            return

        try:
            with open(image_path, 'rb') as image_file:
                files = {'file': (os.path.basename(image_path), image_file, 'image/jpeg')}
                response = requests.post(
                    self.analyze_url,
                    files=files,
                    timeout=self.http_timeout_sec,
                )
                response.raise_for_status()

            self.get_logger().info(f'POST /analyze succeeded for image: {image_path}')
        except requests.RequestException as exc:
            self.get_logger().warning(f'POST /analyze failed: {exc}')


def main(args=None) -> None:
    rclpy.init(args=args)
    node = AGVCommNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
