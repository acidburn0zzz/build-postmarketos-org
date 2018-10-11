<?php

namespace App\Entity;

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
     * @ORM\Column(type="string", length=100)
     */
    private $branch;

    /**
     * @ORM\Column(type="string", length=10)
     */
    private $arch;

    /**
     * @ORM\Column(type="string", length=64)
     */
    private $commit;

    /**
     * @ORM\Column(type="integer")
     */
    private $SrhtId;

    /**
     * @ORM\Column(type="string", length=10)
     */
    private $status;

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

    public function getBranch()
    {
        return $this->branch;
    }

    public function setBranch(string $branch)
    {
        $this->branch = $branch;

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

    public function setCommit(string $commit)
    {
        $this->commit = $commit;

        return $this;
    }

    public function getSrhtId()
    {
        return $this->SrhtId;
    }

    public function setSrhtId(int $SrhtId)
    {
        $this->SrhtId = $SrhtId;

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
}
