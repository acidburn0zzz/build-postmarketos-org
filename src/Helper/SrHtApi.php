<?php

namespace App\Helper;

use Symfony\Component\Yaml\Yaml;

class SrHtApi
{
    private $authorizationToken;
    private $log;

    public function __construct($authorizationToken, LogHelper $log)
    {
        $this->authorizationToken = $authorizationToken;
        $this->log = $log;
    }

    public function SubmitIndexJob($commitSha)
    {
        $manifest = [
            'image' => 'alpine',
            'packages' => 'python3',
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
        $response = \Requests::post($apiUrl, ['Authorization' => $this->authorizationToken], json_encode($job));

        $this->log->write('sent index task to sr.ht', [
            'headers' => $response->headers,
            'code' => $response->status_code,
            'body' => $response->body
        ], true);
        //TODO: Error checking
    }
}