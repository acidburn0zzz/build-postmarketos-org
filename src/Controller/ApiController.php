<?php

namespace App\Controller;

use App\Entity\Queue;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
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
            return new JsonResponse(['error' => 'Gitlab secret missing'], 401);
        }

        if (!hash_equals(sha1($this->getParameter('kernel.secret')), $token)) {
            return new JsonResponse(['error' => 'Secret not correct'], 403);
        }

        $payload = $request->getContent();
        $payload = json_decode($payload, true);

        $event = $request->headers->get('X-Gitlab-Event');

        switch ($event) {
            case 'Push Hook':
                $branch = str_replace('refs/heads/', '', $payload['ref']);
                $this->onNewPush($branch);
                return new JsonResponse(['status' => 'ok']);
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
        if (!$token) {
            return new JsonResponse(['error' => 'Secret missing'], 401);
        }

        if (!hash_equals(sha1($this->getParameter('kernel.secret')), $token)) {
            return new JsonResponse(['error' => 'Secret not correct'], 403);
        }

        $payload = $request->getContent();
        $payload = json_decode($payload, true);

        $this->onNewTask($payload['package'], $payload['pkgver'], $payload['pkgrel'], $payload['commit'], $payload['arch'], $payload['branch']);

        return new JsonResponse(['status' => 'ok']);
    }


    private function onNewPush($branch)
    {
        $srht = $this->get('srht_api');
        $srht->SubmitIndexJob();
        // TODO: Submit task to build server for package diff
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
