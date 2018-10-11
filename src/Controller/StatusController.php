<?php

namespace App\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\Routing\Annotation\Route;

class StatusController extends AbstractController
{
    /**
     * @Route("/", name="status")
     */
    public function index()
    {
        $queue = $this->getDoctrine()->getRepository('App:Queue');
        $queued = $queue->findBy(['status' => ['WAITING', 'BUILDING']], ['id' => 'DESC']);
        $done = $queue->findBy(['status' => ['DONE', 'FAILED']], ['id' => 'DESC'], 50);
        return $this->render('status/index.html.twig', [
            'queued' => $queued,
            'done' => $done
        ]);
    }
}
