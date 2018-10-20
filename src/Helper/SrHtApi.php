<?php

namespace App\Helper;

use Symfony\Component\Yaml\Yaml;

class SrHtApi
{
    private $authorizationToken;

    public function __construct($authorizationToken)
    {
        $this->authorizationToken = $authorizationToken;
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
        if ($response->status_code >= 400) {
            $body = $response->status_code . '\n' . $response->body;
            throw new \Exception($body);
        }
    }
}