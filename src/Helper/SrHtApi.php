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

    public function SubmitIndexJob()
    {
        $manifest = [
            'image' => 'alpine',
            'packages' => 'python3',
            'sources' => [
                'https://gitlab.com/postmarketOS/pmbootstrap.git'
            ],
            'tasks' => [
                'cd pmbootstrap; pmbootstrap dosomething'
            ]
        ];
        $manifest = Yaml::dump($manifest);

        $job = [
            "manifest" => $manifest,
            "note" => ""
        ];

        $response = \Requests::post('', ['Authorization' => $this->authorizationToken], json_encode($job));
    }
}