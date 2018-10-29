<?php

namespace App\Entity;

use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

/**
 * @ORM\Entity(repositoryClass="App\Repository\QueueRepository")
 */
class Queue
{
    /**
     * @ORM\Id()
     * @ORM\GeneratedValue()
     * @ORM\Column(type="integer")
     */
    private $id;

    /**
     * @ORM\Column(type="string", length=100)
     */
    private $aport;

    /**
     * @ORM\Column(type="string", length=100)
     */
    private $pkgver;

    /**
     * @ORM\Column(type="integer")
     */
    private $pkgrel;

    /**
     * @ORM\Column(type="string", length=10)
     */
    private $arch;

    /**
     * @ORM\Column(type="integer")
     */
    private $srhtId;

    /**
     * @ORM\Column(type="string", length=10)
     */
    private $status;

    /**
     * @ORM\OneToMany(targetEntity="App\Entity\QueueDependency", mappedBy="queueItem", orphanRemoval=true)
     */
    private $queueDependencies;

    /**
     * @ORM\ManyToOne(targetEntity="App\Entity\Commit", inversedBy="packages")
     * @ORM\JoinColumn(nullable=false)
     */
    private $commit;

    public function __construct()
    {
        $this->queueDependencies = new ArrayCollection();
    }

    public function getId()
    {
        return $this->id;
    }

    public function getAport()
    {
        return $this->aport;
    }

    public function setAport(string $aport)
    {
        $this->aport = $aport;

        return $this;
    }

    public function getPkgver()
    {
        return $this->pkgver;
    }

    public function setPkgver(string $pkgver)
    {
        $this->pkgver = $pkgver;

        return $this;
    }

    public function getPkgrel()
    {
        return $this->pkgrel;
    }

    public function setPkgrel(int $pkgrel)
    {
        $this->pkgrel = $pkgrel;

        return $this;
    }

    public function getArch()
    {
        return $this->arch;
    }

    public function setArch(string $arch)
    {
        $this->arch = $arch;

        return $this;
    }

    public function getCommit()
    {
        return $this->commit;
    }

    public function setCommit(Commit $commit)
    {
        $this->commit = $commit;

        return $this;
    }

    public function getSrhtId()
    {
        return $this->srhtId;
    }

    public function setSrhtId(int $srhtId)
    {
        $this->srhtId = $srhtId;

        return $this;
    }

    public function getStatus()
    {
        return $this->status;
    }

    public function setStatus(string $status)
    {
        $this->status = $status;

        return $this;
    }

    /**
     * @return Collection|QueueDependency[]
     */
    public function getQueueDependencies()
    {
        return $this->queueDependencies;
    }

    public function addQueueDependency(QueueDependency $queueDependency): self
    {
        if (!$this->queueDependencies->contains($queueDependency)) {
            $this->queueDependencies[] = $queueDependency;
            $queueDependency->setQueueItem($this);
        }

        return $this;
    }

    public function removeQueueDependency(QueueDependency $queueDependency): self
    {
        if ($this->queueDependencies->contains($queueDependency)) {
            $this->queueDependencies->removeElement($queueDependency);
            // set the owning side to null (unless already changed)
            if ($queueDependency->getQueueItem() === $this) {
                $queueDependency->setQueueItem(null);
            }
        }

        return $this;
    }
}
