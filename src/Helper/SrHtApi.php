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
                "version" => "1-r5",
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

        $manifest = [
            'image' => 'alpine/edge',
            'packages' => ['python3', 'coreutils', 'openssl', 'sudo', 'py3-requests'],
            'sources' => [
                'https://gitlab.com/postmarketOS/pmaports.git#' . $commit->getRef()
            ],
            'tasks' => [
                ['setup-pmbootstrap' => 'cd pmaports/.sr.ht; ./install_pmbootstrap.sh'],
                ['check-changes' => 'cd pmaports/.sr.ht; echo \'' . $fakeData . '\' > ~/changes.json'],
                ['submit-to-build' => 'cd pmaports/.sr.ht;COMMIT=' . $commit->getRef() . ' BRANCH=' . $commit->getBranch() . ' python3 submit.py task-submit ~/changes.json']
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

        $this->logger->critical($response->body);
        return 'Submitted job #' . $job_id . ' to sr.ht' . PHP_EOL . PHP_EOL . $manifest;
    }

    public function SubmitBuildJob(Commit $commit, $package, $arch)
    {

        $command = 'pmbootstrap --details-to-stdout --pmaports /home/build/pmaports build --force --strict --arch=' . $arch . ' ' . $package;

        $manifest = [
            'image' => 'alpine/edge',
            'packages' => ['python3', 'coreutils', 'openssl', 'sudo', 'py3-requests'],
            'sources' => [
                'https://gitlab.com/postmarketOS/pmaports.git#' . $commit->getRef()
            ],
            'tasks' => [
                ['setup-pmbootstrap' => 'cd pmaports/.sr.ht; ./install_pmbootstrap.sh'],
                ['build' => 'cd pmaports/.sr.ht; ' . $command],
                ['submit-to-build' => 'cd pmaports/.sr.ht; python3 submit.py task-submit ~/changes.json']
            ],
            'environment' => [
                'COMMIT' => $commit->getRef(),
                'BRANCH' => $commit->getBranch()
            ],
            'secrets' => [$this->secretId],
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

        $this->logger->critical($response->body);
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