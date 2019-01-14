<?php

namespace App\Controller;

use App\Entity\Commit;
use App\Entity\Queue;
use App\Entity\QueueDependency;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\Filesystem\Filesystem;
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

                $message = '';
                if (isset($payload['commits'][0]['message'])) {
                    $message = $payload['commits'][0]['message'];
                }

                $manifest = $this->onNewPush($branch, $payload['checkout_sha'], $message);
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
        $architecture = $request->headers->get('X-Arch');

        if (!$token) {
            $this->get('web_log')->write('task-submit received without secret', null, true);
            return new JsonResponse(['error' => 'Secret missing'], 401);
        }

        if (!hash_equals(sha1($this->getParameter('kernel.secret')), $token)) {
            $this->get('web_log')->write('task-submit received with incorrect secret', null, true);
            return new JsonResponse(['error' => 'Secret not correct'], 403);
        }

        $manager = $this->getDoctrine()->getManager();

        $commit = $this->getDoctrine()->getRepository('App:Commit')->findOneBy(['ref' => $commit]);

        if (!$commit) {
            throw new \Exception('Commit "' . $commit . '" not found in the database');
        }

        if ($commit->getStatus() == 'INDEXING') {
            $commit->setStatus('BUILDING');
        }

        $payload = $request->getContent();
        $payload = json_decode($payload, true);

        if (count($payload) == 0) {
            $commit->setStatus('DONE');
            $manager->flush();
            $this->startNextBuild();
            return new JsonResponse(['status' => 'nothing to be done']);
        }

        $this->get('web_log')->write('task-submit received', $payload);

        $row = [];

        $result = [];

        foreach ($payload as $package) {
            list($pkgver, $pkgrel) = explode('-', $package['version'], 2);
            $pkgrel = (int)str_replace('r', '', $pkgrel);
            $component = $package['repo'];
            $row[$package['pkgname']] = $this->createOrUpdatePackage($package['pkgname'], $pkgver, $pkgrel, $commit, $architecture, $component);
        }

        foreach ($payload as $package) {
            $queueItem = $row[$package['pkgname']];
            $result[] = $package['pkgname'];
            foreach ($package['depends'] as $dependency) {
                if (isset($row[$dependency])) {
                    $queueItemDepend = $row[$dependency];
                    $existing = $this->getDoctrine()->getRepository('App:QueueDependency')->findOneBy(['queueItem' => $queueItem, 'requirement' => $queueItemDepend]);
                    if (!$existing) {
                        $queueDependency = new QueueDependency();
                        $queueDependency->setQueueItem($queueItem);
                        $queueDependency->setRequirement($queueItemDepend);
                        $manager->persist($queueDependency);
                    }
                }
            }
        }

        $manager->flush();

        $this->startNextBuild();

        return new JsonResponse($result);
    }

    /**
     * @Route("/api/package-submit", name="package_submit")
     */
    public function package_submit(Request $request)
    {
        $token = $request->headers->get('X-Secret');
        $commit = $request->headers->get('X-Commit');
        $architecture = $request->headers->get('X-Arch');
        $id = $request->headers->get('X-Id');

        if (!$token) {
            $this->get('web_log')->write('task-submit received without secret', null, true);
            return new JsonResponse(['error' => 'Secret missing'], 401);
        }

        if (!hash_equals(sha1($this->getParameter('kernel.secret')), $token)) {
            $this->get('web_log')->write('task-submit received with incorrect secret', null, true);
            return new JsonResponse(['error' => 'Secret not correct'], 403);
        }

        $manager = $this->getDoctrine()->getManager();

        list($pkgname, $pkgver, $pkgrel) = explode(':', $id, 3);
        $package = $this->getDoctrine()->getRepository('App:Queue')->findOneBy([
            'aport' => $pkgname,
            'pkgver' => $pkgver,
            'pkgrel' => $pkgrel,
            'arch' => $architecture
        ]);

        if (!$package) {
            throw new \Exception('Package "' . $id . '" not found in the database');
        }

        $branch = $package->getCommit()->getBranch();

        $apks = $request->files->get('file');
        foreach ($apks as $apk) {
            $component = $package->getComponent();

            $repository = $this->getParameter('kernel.project_dir') . '/public/repository/' . $branch;

            if (!is_dir($repository)) {
                mkdir($repository);
            }

            $repository .= '/' . $component;
            if (!is_dir($repository)) {
                mkdir($repository);
            }

            if (!is_dir($repository . '/' . $architecture)) {
                mkdir($repository . '/' . $architecture);
            }

            $apk->move($repository . '/' . $architecture . '/', $pkgname . '-' . $pkgver . '-r' . $pkgrel . '.apk');
        }
        $this->rebuildRepositoryIndex($branch, $architecture, $component);

        $package->setStatus('DONE');
        $manager->persist($package);

        $this->get('web_log')->write('package-submit received', [
            'commit' => $commit,
            'architecture' => $architecture,
            'id' => $id
        ]);

        // Check if this completes a commit
        $commitRow = $package->getCommit();
        $commitPackages = $commitRow->getPackages();
        $done = 0;
        $total = count($commitPackages);
        foreach ($commitPackages as $cp) {
            if ($cp->getStatus() == 'DONE') {
                $done++;
            }
        }
        if ($done == $total) {
            $commitRow->setStatus('SIGNING');
            $this->onCommitFinished($commitRow, $branch, $architecture);
        } else {
            $commitRow->setStatus('BUILDING [' . $done . '/' . $total . ']');
        }
        $manager->persist($commitRow);

        $manager->flush();

        $this->startNextBuild();

        return new JsonResponse(['status' => 'ok']);
    }

    /**
     * @Route("/api/signed-submit", name="signed_submit")
     */
    public function signed_submit(Request $request)
    {
        $token = $request->headers->get('X-Secret');
        $commit = $request->headers->get('X-Commit');
        list($component, $arch) = explode('-', $request->headers->get('X-Id'));

        if (!$token) {
            $this->get('web_log')->write('task-submit received without secret', null, true);
            return new JsonResponse(['error' => 'Secret missing'], 401);
        }

        if (!hash_equals(sha1($this->getParameter('kernel.secret')), $token)) {
            $this->get('web_log')->write('task-submit received with incorrect secret', null, true);
            return new JsonResponse(['error' => 'Secret not correct'], 403);
        }

        $commit = $this->getDoctrine()->getRepository('App:Commit')->findOneBy(['ref' => $commit]);

        $offlineRepository = $this->getParameter('kernel.project_dir') . '/public/offlinerepository/' . $commit->getBranch() . '/' . $component . '/' . $arch;

        $apkindex = $request->files->get('file');
        $apkindex->move($offlineRepository, '/APKINDEX.tar.gz');

        $manager = $this->getDoctrine()->getManager();
        $commit->setStatus('DONE');
        $manager->persist($commit);
        $manager->flush();

        return new JsonResponse(['status' => 'ok']);
    }


    private function onCommitFinished(Commit $commit, $branch, $arch)
    {
        $components = [];
        foreach ($commit->getPackages() as $package) {
            $components[] = $package->getComponent();
        }
        $components = array_unique($components);

        foreach ($components as $component) {
            $repository = $this->getParameter('kernel.project_dir') . '/public/repository/' . $branch . '/' . $component . '/' . $arch;
            $offlineRepository = $this->getParameter('kernel.project_dir') . '/public/offlinerepository/' . $branch . '/' . $component . '/' . $arch;

            // Create offline copy of WIP repo
            $filesystem = new Filesystem();
            $filesystem->remove($offlineRepository);
            $filesystem->mkdir($offlineRepository);
            $filesystem->mirror($repository, $offlineRepository);
            $filesystem->remove($offlineRepository . '/APKINDEX.tar.gz');
        }

        $srht = $this->get('srht_api');
        $srht->SubmitSignJob($commit, [$arch], $components);

        //TODO: Prevent concurrent sign jobs
    }

    private function onNewPush($branch, $commit, $message)
    {
        //TODO: remove test code
        //$branch = 'master';
        //$commit = 'f93302d7c8328726c5db959341f42af1b930c78c';

        if ($branch != 'master') {
            $this->get('web_log')->write('Gitlab push is not for master', null, true);
            return 'WRONG BRANCH';
        }
        $srht = $this->get('srht_api');

        $manager = $this->getDoctrine()->getManager();

        $commitObj = $this->getDoctrine()->getRepository('App:Commit')->findOneBy(['ref' => $commit]);
        if (!$commitObj) {
            $commitObj = new Commit();
            $commitObj->setRef($commit);
            $commitObj->setBranch($branch);
            $commitObj->setMessage($message);
            $commitObj->setStatus('INDEXING');
            $manager->persist($commitObj);
        }
        $manager->flush();
        $manifest = $srht->SubmitIndexJob($commitObj);
        return $manifest;
    }

    private function createOrUpdatePackage($package, $pkgver, $pkgrel, Commit $commit, $arch, $component)
    {
        $queue = $this->getDoctrine()->getRepository('App:Queue');
        $manager = $this->getDoctrine()->getManager();

        // Check if there is a running or queued task for this package already
        $existing = $queue->findBy([
            'aport' => $package,
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
                // TODO: Re-link all queue dependencies to new queue item
                $manager->persist($existingTask);
            } else {
                $foundExisting = true;
                break;
            }
        }

        if ($foundExisting) {
            return $existingTask;
        }

        $srht = $this->get('srht_api');
        $id = $srht->SubmitBuildJob($commit, $package, $arch, $package . ':' . $pkgver . ':' . $pkgrel);

        $task = new Queue();
        $task->setAport($package);
        $task->setPkgver($pkgver);
        $task->setPkgrel($pkgrel);
        $task->setArch($arch);
        $task->setCommit($commit);
        $task->setComponent($component);
        $task->setStatus('WAITING');
        $task->setSrhtId($id);
        $manager->persist($task);
        return $task;
    }

    /**
     * @Route("/api/failure-hook", name="failure_hook")
     */
    public function failure_hook(Request $request)
    {
        $payload = $request->getContent();
        $payload = json_decode($payload, true);

        $state = $payload['state'];

        $this->get('web_log')->write('failure-hook ' . $state . ' received', $payload, true);

        if (!in_array($state, ['failed', 'cancelled'])) {
            return new JsonResponse(['ok, no failure then']);
        }

        $manager = $this->getDoctrine()->getManager();
        $queue = $this->getDoctrine()->getRepository('App:Queue');
        $task = $queue->findOneBy(['srhtId' => (int)$payload['id']]);
        if ($task) {
            $this->get('web_log')->write('failure-hook done', 'marking ' . $task->getAport() . ' as failed');
            $task->setStatus('FAILED');
            $manager->persist($task);
            $manager->flush();
        } else {
            $this->get('web_log')->write('failure-hook failure', 'No queue task found for this job');
        }
        $this->startNextBuild();
        return new JsonResponse(['Processed failure']);
    }

    private function startNextBuild()
    {
        $manager = $this->getDoctrine()->getManager();
        $queue = $this->getDoctrine()->getRepository('App:Queue');

        $running = $queue->findOneBy(['status' => 'BUILDING']);

        if ($running) {
            return;
        }

        $next = $queue->getStartable();

        $this->get('web_log')->write('next-build startables', $next);

        if (count($next) > 0) {
            $srht = $this->get('srht_api');
            $srht->StartJob($next[0]->getSrhtId());
            $next[0]->setStatus('BUILDING');
            $manager->persist($next[0]);
            $manager->flush();
        }
    }

    private function rebuildRepositoryIndex($branch, $arch, $component)
    {
        $repository = $this->getParameter('kernel.project_dir') . '/public/repository/' . $branch . '/' . $component . '/' . $arch;

        $descriptors = [
            0 => ['pipe', 'r'],
            1 => ['pipe', 'w'],
            2 => ['pipe', 'w']
        ];
        $binary = $this->getParameter('kernel.project_dir') . '/tools/apk.static';
        $command = $binary . ' -q index --output APKINDEX.tar.gz_ --rewrite-arch ' . $arch . ' *.apk';
        $p = proc_open($command, $descriptors, $pipes, $repository);
        if (is_resource($p)) {
            // Close stdin
            fclose($pipes[0]);

            // Get output
            $output = stream_get_contents($pipes[1]);
            fclose($pipes[1]);

            // Get stderr
            $errors = stream_get_contents($pipes[2]);
            fclose($pipes[2]);

            $return_value = proc_close($p);
        }

        $this->get('web_log')->write('apk-index', [
            'stdout' => $output,
            'stderr' => $errors,
            'return' => $return_value,
        ]);
        $this->signRepository($branch, $arch, $component);
    }

    private function signRepository($branch, $arch, $component)
    {
        $repository = $this->getParameter('kernel.project_dir') . '/public/repository/' . $branch . '/' . $component . '/' . $arch;

        $descriptors = [
            0 => ['pipe', 'r'],
            1 => ['pipe', 'w'],
            2 => ['pipe', 'w']
        ];
        $binary = $this->getParameter('kernel.project_dir') . '/tools/abuild-sign.noinclude';
        $privkey = $this->getParameter('kernel.project_dir') . '/private/build@postmarketos.org.rsa';
        $index = $repository . '/APKINDEX.tar.gz_';
        $command = $binary . ' -p build@postmarketos.org.pub -k "' . $privkey . '" "' . $index . '"';
        $p = proc_open($command, $descriptors, $pipes, $repository);
        if (is_resource($p)) {
            // Close stdin
            fclose($pipes[0]);

            // Get output
            $output = stream_get_contents($pipes[1]);
            fclose($pipes[1]);

            // Get stderr
            $errors = stream_get_contents($pipes[2]);
            fclose($pipes[2]);

            $return_value = proc_close($p);
        }

        $this->get('web_log')->write('apk-index', [
            'stdout' => $output,
            'stderr' => $errors,
            'return' => $return_value,
        ]);

        $finalIndex = str_replace('.tar.gz_', '.tar.gz', $index);
        rename($index, $finalIndex);
    }
}
