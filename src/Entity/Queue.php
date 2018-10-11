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

    public function getId(): ?int
    {
        return $this->id;
    }

    public function getAport(): ?string
    {
        return $this->aport;
    }

    public function setAport(string $aport): self
    {
        $this->aport = $aport;

        return $this;
    }

    public function getPkgver(): ?string
    {
        return $this->pkgver;
    }

    public function setPkgver(string $pkgver): self
    {
        $this->pkgver = $pkgver;

        return $this;
    }

    public function getPkgrel(): ?int
    {
        return $this->pkgrel;
    }

    public function setPkgrel(int $pkgrel): self
    {
        $this->pkgrel = $pkgrel;

        return $this;
    }

    public function getBranch(): ?string
    {
        return $this->branch;
    }

    public function setBranch(string $branch): self
    {
        $this->branch = $branch;

        return $this;
    }

    public function getArch(): ?string
    {
        return $this->arch;
    }

    public function setArch(string $arch): self
    {
        $this->arch = $arch;

        return $this;
    }

    public function getCommit(): ?string
    {
        return $this->commit;
    }

    public function setCommit(string $commit): self
    {
        $this->commit = $commit;

        return $this;
    }

    public function getSrhtId(): ?int
    {
        return $this->SrhtId;
    }

    public function setSrhtId(int $SrhtId): self
    {
        $this->SrhtId = $SrhtId;

        return $this;
    }

    public function getStatus(): ?string
    {
        return $this->status;
    }

    public function setStatus(string $status): self
    {
        $this->status = $status;

        return $this;
    }
}
