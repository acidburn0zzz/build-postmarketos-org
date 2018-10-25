<?php

namespace App\Controller;

use App\Entity\Queue;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;

class ApiController extends Controller
{
    /**
     * @Route("/api/pull-hook/gitlab", name="gitlab_pull")
     */
    public function gitlab_pull(Request $request)
    {
        $token = $request->headers->get('X-Gitlab-Token');
        if (!$token) {
            $this->get('web_log')->write('gitlab-pull received without secret', null, true);
            return new JsonResponse(['error' => 'Gitlab secret missing'], 401);
        }


        if (!hash_equals(sha1($this->getParameter('kernel.secret')), $token)) {
            $this->get('web_log')->write('gitlab-pull received with incorrect secret', null, true);
            return new JsonResponse(['error' => 'Secret not correct'], 403);
        }

        $payload = $request->getContent();
        $payload = json_decode($payload, true);

        $this->get('web_log')->write('gitlab-pull received', $payload, true);

        $event = $request->headers->get('X-Gitlab-Event');

        switch ($event) {
            case 'Push Hook':
                $branch = str_replace('refs/heads/', '', $payload['ref']);
                $manifest = $this->onNewPush($branch, $payload['checkout_sha']);
                return new Response($manifest);
                break;
        }
        return new JsonResponse(['error' => 'Unknown event "' . $event . '"'], 400);
    }

    /**
     * @Route("/api/task-submit", name="task_submit")
     */
    public function task_submit(Request $request)
    {
        $token = $request->headers->get('X-Secret');
        $commit = $request->headers->get('X-Commit');
        $branch = $request->headers->get('X-Branch');
        if (!$token) {
            $this->get('web_log')->write('task-submit received without secret', null, true);
            return new JsonResponse(['error' => 'Secret missing'], 401);
        }

        if (!hash_equals(sha1($this->getParameter('kernel.secret')), $token)) {
            $this->get('web_log')->write('task-submit received with incorrect secret', null, true);
            return new JsonResponse(['error' => 'Secret not correct'], 403);
        }

        $payload = $request->getContent();
        $payload = json_decode($payload, true);

        $this->get('web_log')->write('task-submit received', $payload);

        foreach ($payload as $architecture => $packages) {
            foreach ($packages as $package) {
                list($pkgver, $pkgrel) = explode('-', $package['pkgver'], 2);
                $pkgrel = (int)str_replace('r', '', $pkgrel);
                $this->onNewTask($package['pkgname'], $pkgver, $pkgrel, $commit, $architecture, $branch);
            }
        }

        return new JsonResponse(['status' => 'ok']);
    }


    private function onNewPush($branch, $commit)
    {
        if ($branch != 'master') {
            $this->get('web_log')->write('Gitlab push is not for master', null, true);
            return 'WRONG BRANCH';
        }
        $srht = $this->get('srht_api');
        $manifest = $srht->SubmitIndexJob($commit);
        return $manifest;
    }

    private function onNewTask($package, $pkgver, $pkgrel, $commit, $arch, $branch)
    {
        $queue = $this->getDoctrine()->getRepository('App:Queue');
        $manager = $this->getDoctrine()->getManager();

        // Check if there is a running or queued task for this package already
        $existing = $queue->findBy([
            'aport' => $package,
            'branch' => $branch,
            'arch' => $arch,
            'status' => ['WAITING', 'BUILDING']
        ]);
        $foundExisting = false;
        foreach ($existing as $existingTask) {
            if ($existingTask->getPkgver() != $pkgver || $existingTask->getPkgrel() != $pkgrel) {
                if ($existingTask->getStatus() == 'BUILDING') {
                    // TODO: Kill existing task at sr.ht with id $existingTask->getSrhtId()
                }
                $existingTask->setStatus('SUPERSEDED');
                $manager->persist($existingTask);
            } else {
                $foundExisting = true;
            }
        }

        if ($foundExisting) {
            $task = new Queue();
            $task->setAport($package);
            $task->setPkgver($pkgver);
            $task->setPkgrel($pkgrel);
            $task->setBranch($branch);
            $task->setArch($arch);
            $task->setCommit($commit);
            $task->setStatus('WAITING');
            $task->setSrhtId(0);
            $manager->persist($task);
            // TODO: Submit task to sr.ht and write correct ID back
        }
        $manager->flush();
    }
}
