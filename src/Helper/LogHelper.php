<?php

namespace App\Helper;


use App\Entity\Log;

class LogHelper
{
    private $doctrine;

    public function __construct($doctrine)
    {
        $this->doctrine = $doctrine;
    }

    public function write($action, $detail = null, $flush = false)
    {
        if (is_array($detail) || is_object($detail)) {
            $detail = json_encode($detail, JSON_PRETTY_PRINT);
        }

        $message = new Log();
        $message->setDatetime(new \DateTime());
        $message->setAction($action);
        $message->setDetails($detail);
        $this->doctrine->persist($message);

        if($flush){
            $this->doctrine->flush();
        }
    }
}