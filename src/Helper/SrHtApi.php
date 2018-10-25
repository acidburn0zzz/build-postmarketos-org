<?php

namespace App\Helper;

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

    public function SubmitIndexJob($commitSha)
    {
        $commitSha = '70f8342ce08fbb9501cd7e618d6aa275f7217c90';
        $manifest = [
            'image' => 'alpine/edge',
            'packages' => ['python3', 'coreutils', 'openssl', 'sudo', 'py3-requests'],
            'sources' => [
                'https://gitlab.com/postmarketOS/pmaports.git#' . $commitSha
            ],
            'tasks' => [
                ['setup-pmbootstrap' => 'cd pmaports/.sr.ht; sudo ./install_pmbootstrap.sh'],
                ['check-changes' => 'echo \'{ "x86_64": [{"pkgname": "hello-world", "version": "1-r4"}, {"pkgname": "devicepkg-dev", "version": "0.5-r0"}]}
\' > changes.json'],
                ['submit-to-build' => 'python3 submit.py task-submit changes.json']
            ],
            'secrets' => [$this->secretId]
        ];
        $manifest = Yaml::dump($manifest);

        $url = 'https://gitlab.com/postmarketOS/pmaports/commit/' . $commitSha;

        $job = [
            "manifest" => $manifest,
            "note" => "Dependency check job for [" . $commitSha . "](" . $url . ")"
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
}