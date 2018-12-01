<?php

namespace App\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\Routing\Annotation\Route;

class StatusController extends AbstractController
{
    /**
     * @Route("/", name="status")
     * @Route("/packages", name="packages")
     */
    public function packages()
    {
        $queue = $this->getDoctrine()->getRepository('App:Queue');
        $queued = $queue->findBy(['status' => ['WAITING', 'BUILDING']], ['id' => 'DESC']);
        $done = $queue->findBy(['status' => ['DONE', 'FAILED', 'SUPERSEDED']], ['id' => 'DESC'], 50);
        return $this->render('status/packages.html.twig', [
            'queued' => $queued,
            'done' => $done
        ]);
    }

    /**
     * @Route("/commits", name="commits")
     */
    public function commits()
    {
        $queue = $this->getDoctrine()->getRepository('App:Commit');
        $queued = $queue->findBy(['status' => ['INDEXING', 'BUILDING', 'SIGNING']], ['id' => 'DESC']);
        $done = $queue->findBy(['status' => ['DONE', 'FAILED', 'SUPERSEDED']], ['id' => 'DESC'], 50);
        return $this->render('status/commits.html.twig', [
            'queued' => $queued,
            'done' => $done
        ]);
    }

    /**
     * @Route("/log", name="log")
     */
    public function log()
    {
        $log = $this->getDoctrine()->getRepository('App:Log')->findBy([], ['datetime' => 'DESC']);
        return $this->render('status/log.html.twig', [
            'log' => $log,
        ]);
    }
}
