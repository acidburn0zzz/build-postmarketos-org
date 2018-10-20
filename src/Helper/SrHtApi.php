<?php

namespace App\Helper;

use Psr\Log\LoggerInterface;
use Symfony\Component\Yaml\Yaml;

class SrHtApi
{
    private $authorizationToken;
    private $logger;

    public function __construct($authorizationToken, LoggerInterface $logger)
    {
        $this->authorizationToken = $authorizationToken;
        $this->logger = $logger;
    }

    public function SubmitIndexJob($commitSha)
    {
        $manifest = [
            'image' => 'alpine',
            'packages' => ['python3'],
            'sources' => [
                'https://gitlab.com/postmarketOS/pmbootstrap.git'
            ],
            'tasks' => [
                'cd pmbootstrap; pmbootstrap dosomething ' . $commitSha //TODO: Add implementation inside pmbootstrap
            ]
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
    }
}