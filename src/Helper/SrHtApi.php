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

    public function __construct($authorizationToken, LoggerInterface $logger, $secretId)
    {
        $this->authorizationToken = $authorizationToken;
        $this->logger = $logger;
        $this->secretId = $secretId;
    }

    public function SubmitIndexJob(Commit $commit)
    {
        //TODO: Remove, testing code
        $fakeData = [
            [
                "pkgname" => "hello-world",
                "repo" => "main",
                "version" => "1-r4",
                "depends" => []
            ],
            [
                "pkgname" => "hello-world-wrapper",
                "repo" => "main",
                "version" => "1-r2",
                "depends" => ["hello-world"]
            ]
        ];
        $fakeData = json_encode($fakeData);

        $command = 'pmbootstrap -q --aports /home/build/pmaports repo_missing > ~/changes.json';

        $manifest = [
            'image' => 'alpine/edge',
            'packages' => ['python3', 'coreutils', 'openssl', 'wget', 'sudo', 'py3-requests'],
            'sources' => [
                'https://gitlab.com/postmarketOS/pmaports.git#' . $commit->getRef()
            ],
            'tasks' => [
                ['setup-pmbootstrap' => 'cd pmaports/.sr.ht; ./install_pmbootstrap.sh'],
                ['check-changes' => 'cd pmaports/.sr.ht; ' . $command],
                ['submit-to-build' => 'cd pmaports/.sr.ht; python3 submit.py --json task-submit ~/changes.json']
            ],
            'environment' => [
                'COMMIT' => $commit->getRef(),
                'BRANCH' => $commit->getBranch()
            ],
            'secrets' => [$this->secretId]
        ];
        $manifest = Yaml::dump($manifest);

        $url = 'https://gitlab.com/postmarketOS/pmaports/commit/' . $commit->getRef();

        $job = [
            "manifest" => $manifest,
            "note" => "Dependency check job for [" . $commit->getRef() . "](" . $url . ")"
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
        return 'Submitted job #' . $job_id . ' to sr.ht' . PHP_EOL . PHP_EOL . $manifest;
    }

    public function SubmitBuildJob(Commit $commit, $package, $arch, $id)
    {

        $command = 'pmbootstrap --details-to-stdout --aports /home/build/pmaports build --force --strict --arch=' . $arch . ' ' . $package;

        $manifest = [
            'image' => 'alpine/edge',
            'packages' => ['python3', 'coreutils', 'openssl', 'wget', 'sudo', 'py3-requests'],
            'sources' => [
                'https://gitlab.com/postmarketOS/pmaports.git#' . $commit->getRef()
            ],
            'tasks' => [
                ['setup-pmbootstrap' => 'cd pmaports/.sr.ht; ./install_pmbootstrap.sh'],
                ['add-key' => 'cd ~/.local/var/pmbootstrap/config_apk_keys/ ; cp ~/.secrets/build@postmarketos.org.priv . ; openssl rsa -in build@postmarketos.org.priv -pubout build@postmarketos.org.pub'],
                ['build' => 'cd pmaports/.sr.ht; ' . $command],
                ['submit-to-build' => 'cd pmaports/.sr.ht; python3 submit.py --id ' . $id . ' package-submit ~/.local/var/pmbootstrap/packages/' . $arch . '/' . $package . '-*-r*.apk']
            ],
            'environment' => [
                'COMMIT' => $commit->getRef(),
                'BRANCH' => $commit->getBranch(),
            ],
            'secrets' => [$this->secretId, '6c3dd41b-f158-4a8b-b372-1da4daaeb4d2'],
            'triggers' => [
                [
                    'action' => 'webhook',
                    'condition' => 'failure',
                    'url' => 'https://build.postmarketos.org/api/failure-hook'
                ]
            ]
        ];

        $manifest = Yaml::dump($manifest);

        $url = 'https://gitlab.com/postmarketOS/pmaports/commit/' . $commit->getRef();

        $note = 'Building ' . $package . '[' . $arch . '] from commit [' . $commit->getRef() . '](' . $url . ')';

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
}