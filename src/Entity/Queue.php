<?php

namespace App\Entity;

use DateTime;
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
     * @ORM\ManyToOne(targetEntity="App\Entity\Package", inversedBy="versions")
     * @ORM\JoinColumn(nullable=false)
     */
    private $package;

    /**
     * @ORM\Column(type="string", length=100)
     */
    private $pkgver;

    /**
     * @ORM\Column(type="integer")
     */
    private $pkgrel;

    /**
     * @ORM\Column(type="integer", nullable=true)
     */
    private $srhtId;

    /**
     * @ORM\Column(type="string", length=10)
     */
    private $status;

    /**
     * @ORM\ManyToOne(targetEntity="App\Entity\Commit", inversedBy="packages")
     * @ORM\JoinColumn(nullable=false)
     */
    private $commit;

    /**
     * @ORM\Column(type="integer", nullable=true)
     */
    private $timeSpent;

    /**
     * @ORM\Column(type="datetime", nullable=true)
     */
    private $timeStarted;



    public function getId()
    {
        return $this->id;
    }

    /**
     * @return Package
     */
    public function getPackage()
    {
        return $this->package;
    }

    /**
     * @param Package $package
     */
    public function setPackage($package)
    {
        $this->package = $package;
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

    /**
     * @return Commit
     */
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
     * @return mixed
     */
    public function getTimeSpent()
    {
        return $this->timeSpent;
    }

    /**
     * @param mixed $timeSpent
     */
    public function setTimeSpent($timeSpent)
    {
        $this->timeSpent = $timeSpent;
    }

    /**
     * @return datetime
     */
    public function getTimeStarted()
    {
        return $this->timeStarted;
    }

    /**
     * @param datetime $timeStarted
     */
    public function setTimeStarted($timeStarted)
    {
        $this->timeStarted = $timeStarted;
    }
}
