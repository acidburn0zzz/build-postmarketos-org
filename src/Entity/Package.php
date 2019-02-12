<?php

namespace App\Entity;

use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

/**
 * @ORM\Entity(repositoryClass="App\Repository\PackageRepository")
 */
class Package
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
     * @ORM\Column(type="string", length=10)
     */
    private $arch;

    /**
     * @ORM\Column(type="string", length=30)
     */
    private $component;

    /**
     * @ORM\OneToMany(targetEntity="App\Entity\PackageDependency", mappedBy="package", orphanRemoval=true)
     */
    private $packageDependencies;

    /**
     * @ORM\OneToMany(targetEntity="App\Entity\Queue", mappedBy="package", orphanRemoval=true)
     */
    private $versions;

    /**
     * @ORM\Column(type="bigint", nullable=true)
     */
    private $timeSpent;

    /**
     * @ORM\Column(type="integer", nullable=true)
     */
    private $timesBuilt;


    public function __construct()
    {
        $this->packageDependencies = new ArrayCollection();
    }

    /**
     * @return mixed
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * @param mixed $id
     */
    public function setId($id)
    {
        $this->id = $id;
    }

    /**
     * @return mixed
     */
    public function getAport()
    {
        return $this->aport;
    }

    /**
     * @param mixed $aport
     */
    public function setAport($aport)
    {
        $this->aport = $aport;
    }

    /**
     * @return mixed
     */
    public function getArch()
    {
        return $this->arch;
    }

    /**
     * @param mixed $arch
     */
    public function setArch($arch)
    {
        $this->arch = $arch;
    }


    /**
     * @return Collection|PackageDependency[]
     */
    public function getQueueDependencies()
    {
        return $this->packageDependencies;
    }

    public function addQueueDependency(PackageDependency $queueDependency): self
    {
        if (!$this->packageDependencies->contains($queueDependency)) {
            $this->packageDependencies[] = $queueDependency;
            $queueDependency->setPackage($this);
        }

        return $this;
    }

    public function removeQueueDependency(PackageDependency $queueDependency): self
    {
        if ($this->packageDependencies->contains($queueDependency)) {
            $this->packageDependencies->removeElement($queueDependency);
            // set the owning side to null (unless already changed)
            if ($queueDependency->getPackage() === $this) {
                $queueDependency->setPackage(null);
            }
        }

        return $this;
    }

    /**
     * @return string
     */
    public function getComponent()
    {
        return $this->component;
    }

    /**
     * @param string $component
     */
    public function setComponent($component)
    {
        $this->component = $component;
    }

    /**
     * @return Queue[]
     */
    public function getVersions()
    {
        return $this->versions;
    }

    /**
     * @param mixed $versions
     */
    public function setVersions($versions)
    {
        $this->versions = $versions;
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
     * @return mixed
     */
    public function getTimesBuilt()
    {
        return $this->timesBuilt;
    }

    /**
     * @param mixed $timesBuilt
     */
    public function setTimesBuilt($timesBuilt)
    {
        $this->timesBuilt = $timesBuilt;
    }

    public function getAverageBuildTime()
    {
        return new \DateInterval(($this->timeSpent / $this->timesBuilt) . ' seconds');
    }
}
