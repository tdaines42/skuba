import argparse
import logging
import os
import subprocess

logger = logging.getLogger('Deploy-Kubeflow')


class DeployKubeflow:

    def deploy_kubeflow(self, config_path, config_url, kubeconfig):
        kubeflow_path = os.join(config_path, 'kubeflow')
        os.makedirs(kubeflow_path, exist_ok=True)
        # Setup the config
        self._run_cmd(f'kfctl apply -V -f {config_url}', cwd=kubeflow_path)

        # Wait for kubeflow to be ready
        self._run_cmd(f'kubectl --kubeconfig {kubeconfig} wait --for=condition=ready pods -n kubeflow --all --timeout 5m')

        return kubeflow_path

    def create_kubeflow_psp(self, psp_path):
        if not os.path.isfile(psp_path):
            raise FileNotFoundError(psp_path)

        self._run_cmd(f'kubectl -n kubeflow create {psp_path}')

    def _run_cmd(self, cmd, cwd=None):
        logger.debug(cmd)

        proc = subprocess.run(cmd,
                              cwd=cwd,
                              encoding='utf8',
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT)
        if proc.returncode != 0:
            raise Exception(f'Received exit code {proc.returncode} while running command {cmd}\n{proc.stdout}')

        return proc.stdout


def define_parser(parser):
    parser.add_argument('--kubeconfig', default=os.environ.get('KUBECONFIG'),
                        help='Path to kubeconfig file')

    parser.add_argument('--psp-path',
                        default=os.path.join(os.cwd(), "kubeflow-psp.yaml"),
                        help='Path to the psp')

    parser.add_argument('--config-url',
                        default='https://raw.githubusercontent.com/SUSE/manifests/v1.0-branch-caasp/kfdef/kfctl_caasp.yaml',
                        help='URL for the kubeflow config')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deploy kubeflow to a CaaSP cluster')
    define_parser(parser)
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(name)s: %(levelname)s: %(message)s', level='DEBUG' if args.debug else 'INFO')

    deploy = DeployKubeflow()
    deploy.create_kubeflow_psp(args.psp_path)
    deploy.deploy_kubeflow(os.cwd(), args.config_url, args.kubeconfig)
