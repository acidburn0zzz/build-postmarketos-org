<?php


namespace App\Tests\Repository;

use App\Repository\QueueRepository;
use Symfony\Bundle\FrameworkBundle\Test\KernelTestCase;

class QueueRepositoryTest extends KernelTestCase
{
    /**
     * @var \Doctrine\ORM\EntityManager
     */
    private $entityManager;

    protected function setUp()
    {
        $kernel = self::bootKernel();
        $this->entityManager = $kernel->getContainer()->get('doctrine')->getManager();
    }

    protected function tearDown()
    {
        parent::tearDown();

        $this->entityManager->close();
        $this->entityManager = null; // avoid memory leaks
    }

    public function testGetStartable()
    {
        $queue = $this->entityManager->getRepository('App:Queue');
        $startable = $queue->getStartable();

        $this->assertEquals($startable, []);
    }

}