<?php

namespace App\Entity;

use Doctrine\ORM\Mapping as ORM;

/**
 * @ORM\Entity(repositoryClass="App\Repository\QueueDependencyRepository")
 */
class QueueDependency
{
    /**
     * @ORM\Id()
     * @ORM\GeneratedValue()
     * @ORM\Column(type="integer")
     */
    private $id;

    /**
     * @ORM\ManyToOne(targetEntity="App\Entity\Queue", inversedBy="queueDependencies")
     * @ORM\JoinColumn(nullable=false)
     */
    private $queueItem;

    /**
     * @ORM\ManyToOne(targetEntity="App\Entity\Queue")
     * @ORM\JoinColumn(nullable=false)
     */
    private $requirement;

    public function getId()
    {
        return $this->id;
    }

    public function getQueueItem()
    {
        return $this->queueItem;
    }

    public function setQueueItem(Queue $queueItem): self
    {
        $this->queueItem = $queueItem;

        return $this;
    }

    public function getRequirement()
    {
        return $this->requirement;
    }

    public function setRequirement(Queue $requirement)
    {
        $this->requirement = $requirement;

        return $this;
    }
}
