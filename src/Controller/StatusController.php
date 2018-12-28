<?php

namespace App\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;

class StatusController extends Controller
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
     * @Route("/commits/{ref}", name="commit_details")
     */
    public function commitDetails($ref)
    {
        $commits = $this->getDoctrine()->getRepository('App:Commit');
        $commit = $commits->findOneBy(['ref' => $ref]);
        $packages = $commit->getPackages();

        $graph = 'digraph g {' . PHP_EOL . '    rankdir=LR;' . PHP_EOL;
        foreach ($packages as $package) {
            $label = $package->getAport() . ' ' . $package->getPkgver() . '-r' . $package->getPkgrel();
            switch ($package->getStatus()) {
                case "WAITING":
                    $color = 'azure1';
                    break;
                case "BUILDING":
                    $color = 'azure3';
                    break;
                case "FAILED":
                    $color = 'tomato';
                    break;
                case "DONE":
                    $color = 'darkolivegreen1';
                    break;
                case "SUPERSEDED":
                    $color = 'blanchedalmond'; //because why not
                    break;
            }
            $graph .= '    pkg' . $package->getAport() . '[label="' . $label . '" fillcolor=' . $color . ']' . PHP_EOL;
        }
        $graph .= PHP_EOL . PHP_EOL;
        foreach ($packages as $package) {
            foreach ($package->getQueueDependencies() as $dependency) {
                $graph .= '    pkg' . $dependency->getQueueItem()->getAport() . ' -> pkg' . $package->getAport() . PHP_EOL;
            }
        }
        $graph .= ' }';

        $tempFile = tempnam('/tmp', 'pmosbld-');
        $outFile = $this->getParameter('kernel.project_dir') . '/public/commit/' . $ref . '.png';
        file_put_contents($tempFile, $graph);
        exec('dot "' . $tempFile . '" -o "' . $outFile . '" -Tpng');

        return $this->render('status/commit.html.twig', ['ref' => $ref]);
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
