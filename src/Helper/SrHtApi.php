<?php

namespace App\Helper;

use App\Entity\Commit;
use Psr\Log\LoggerInterface;
use Symfony\Component\Yaml\Yaml;

class SrHtApi
{
    private $authorizationToken;
    private $logger;
    private $secretId;

    private $secretBuildKey = '27bee529-aeb8-4241-b57b-db7e7b8c581d';
    private $secretRepositoryKey = '0d142563-7cb0-4396-b70c-aacc5a89cac1';

    public function __construct($authorizationToken, LoggerInterface $logger, $secretId)
    {
        $this->authorizationToken = $authorizationToken;
        $this->logger = $logger;
        $this->secretId = $secretId;
    }

    public function SubmitIndexJob(Commit $commit)
    {
        $tasks = [
            [
                'setup-pmbootstrap',
                'cd pmaports/.sr.ht',
                './install_pmbootstrap.sh'
            ],
            [
                'check-changes',
                'cd pmaports/.sr.ht',
                'pmbootstrap --aports /home/build/pmaports repo_missing > ~/changes.json',
                'cat ~/changes.json'
            ],
            [
                'submit',
                'cd pmaports/.sr.ht',
                'python3 submit.py --json task-submit ~/changes.json'
            ]
        ];

        $url = 'https://gitlab.com/postmarketOS/pmaports/commit/' . $commit->getRef();
        $note = "Dependency check job for [" . $commit->getRef() . "](" . $url . ")";

        return $this->submitJob($commit, $tasks, [], $note);
    }

    public function SubmitBuildJob(Commit $commit, $package, $arch, $id)
    {
        $tasks = [
            [
                'setup-pmbootstrap',
                'cd pmaports/.sr.ht',
                './install_pmbootstrap.sh'
            ],
            [
                'add-key',
                'mkdir ~/.local/var/pmbootstrap/config_abuild',
                'cd ~/.local/var/pmbootstrap/config_abuild/',
                'cp ~/.secrets/build@postmarketos.org.priv .',
                'openssl rsa -in build@postmarketos.org.priv -pubout -out build@postmarketos.org.pub',
                'echo PACKAGER_PRIVKEY="/home/pmos/.abuild/build@postmarketos.org.priv" > abuild.conf'
            ],
            [
                'build',
                'cd pmaports/.sr.ht',
                'pmbootstrap --details-to-stdout --aports /home/build/pmaports build --force --strict --arch=' . $arch . ' ' . $package
            ],
            [
                'submit',
                'cd pmaports/.sr.ht',
                'python3 submit.py --id ' . $id . ' package-submit ~/.local/var/pmbootstrap/packages/' . $arch . '/' . $package . '-*-r*.apk'
            ]
        ];

        $url = 'https://gitlab.com/postmarketOS/pmaports/commit/' . $commit->getRef();
        $note = 'Building ' . $package . '[' . $arch . '] from commit [' . $commit->getRef() . '](' . $url . ')';

        return $this->submitJob($commit, $tasks, [$this->secretBuildKey], $note);
    }

    public function SubmitSignJob(Commit $commit, $architectures, $components)
    {
        $tasks = [
            [
                'add-key',
                'cd /etc/apk/keys',
                'cp ~/.secrets/repository@postmarketos.org.rsa .',
                'openssl rsa -in repository@postmarketos.org.rsa -pubout -out repository@postmarketos.org.pub',
            ]
        ];

        foreach ($architectures as $arch) {
            foreach ($components as $component) {
                $tasks[] = [
                    'sign-' . $component . '-' . $arch,
                    'wget https://build.postmarketos.org/repository/' . $commit->getBranch() . '/' . $component . '/' . $arch . '/APKINDEX.tar.gz',
                    'abuild-sign -k /etc/apk/keys/repository@postmarketos.org.rsa -p repository@postmarketos.org.pub APKINDEX.tar.gz',
                    'cd pmaports/.sr.ht',
                    'python3 submit.py --id ' . $component . '-' . $arch . ' signed-submit ~/APKINDEX.tar.gz',
                    'rm -rf ~/APKINDEX.tar.gz'
                ];
            }
        }

        $url = 'https://gitlab.com/postmarketOS/pmaports/commit/' . $commit->getRef();
        $note = "Signing job for [" . $commit->getRef() . "](" . $url . ")";

        return $this->submitJob($commit, $tasks, [$this->secretRepositoryKey], $note);
    }

    public function StartJob($id)
    {
        $apiUrl = 'http://builds.sr.ht/api/jobs/' . $id . '/start';
        $response = \Requests::post($apiUrl, [
            'Authorization' => 'token ' . $this->authorizationToken,
            'Content-Type' => 'application/json'
        ], '{}');

        if ($response->status_code >= 400) {
            $this->logger->error('Response status code: ' . $response->status_code);
            throw new \Exception($response->body);
        }
    }

    private function submitJob(Commit $commit, $tasks, $secrets, $note)
    {
        $manifest = [
            'image' => 'alpine/edge',
            'packages' => ['python3', 'coreutils', 'openssl', 'wget', 'sudo', 'py3-requests'],
            'sources' => [
                'https://gitlab.com/postmarketOS/pmaports.git#' . $commit->getRef()
            ],
            'tasks' => [],
            'environment' => [
                'COMMIT' => $commit->getRef(),
                'BRANCH' => $commit->getBranch(),
            ],
            'secrets' => [$this->secretId] + $secrets,
            'triggers' => [
                [
                    'action' => 'webhook',
                    'condition' => 'failure',
                    'url' => 'https://build.postmarketos.org/api/failure-hook'
                ]
            ]
        ];

        foreach ($tasks as $label => $commands) {
            $manifest['tasks'][$label] = implode(' ; ', $commands);
        }

        $manifest = Yaml::dump($manifest);
        $job = [
            "manifest" => $manifest,
            "note" => $note,
            "execute" => false
        ];

        $apiUrl = 'http://builds.sr.ht/api/jobs';

        $this->logger->info('Sending POST request to "' . $apiUrl . '"');
        $this->logger->info('Using token ' . $this->authorizationToken);

        $response = \Requests::post($apiUrl, [
            'Authorization' => 'token ' . $this->authorizationToken,
            'Content-Type' => 'application/json'
        ], json_encode($job));

        if ($response->status_code >= 400) {
            $this->logger->error('Response status code: ' . $response->status_code);
            throw new \Exception($response->body);
        }

        $response = json_decode($response->body, true);
        $job_id = $response['id'];

        $this->logger->critical($response);
        return $job_id;
    }
}